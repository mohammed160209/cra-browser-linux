#include "browser.h"

#include <algorithm>
#include <filesystem>
#include <functional>
#include <iostream>
#include <map>
#include <memory>
#include <string>
#include <utility>

#include "session.h"
#include "include/cef_app.h"
#include "include/cef_display_handler.h"
#include "include/cef_download_handler.h"
#include "include/cef_focus_handler.h"
#include "include/cef_request_context.h"
#include "include/cef_life_span_handler.h"
#include "include/cef_load_handler.h"
#include "include/views/cef_box_layout.h"
#include "include/views/cef_fill_layout.h"
#include "include/views/cef_browser_view.h"
#include "include/views/cef_browser_view_delegate.h"
#include "include/views/cef_label_button.h"
#include "include/views/cef_scroll_view.h"
#include "include/views/cef_textfield.h"
#include "include/views/cef_textfield_delegate.h"
#include "include/views/cef_window.h"
#include "include/views/cef_window_delegate.h"
#include "include/cef_task.h"

namespace cra {
namespace {

class UiTask : public CefTask {
 public:
  explicit UiTask(std::function<void()> action) : action_(std::move(action)) {}
  void Execute() override { action_(); }
 private:
  std::function<void()> action_;
  IMPLEMENT_REFCOUNTING(UiTask);
};

class Button : public CefButtonDelegate {
 public:
  explicit Button(std::function<void()> action) : action_(std::move(action)) {}
  void OnButtonPressed(CefRefPtr<CefButton>) override {
    auto action = action_;
    action();
  }
 private:
  std::function<void()> action_;
  IMPLEMENT_REFCOUNTING(Button);
};

class Entry : public CefTextfieldDelegate {
 public:
  explicit Entry(std::function<void(std::string)> submit) : submit_(std::move(submit)) {}
  bool OnKeyEvent(CefRefPtr<CefTextfield> field, const CefKeyEvent& event) override {
    if (event.type != KEYEVENT_RAWKEYDOWN || event.windows_key_code != 13) return false;
    submit_(field->GetText());
    return true;
  }
 private:
  std::function<void(std::string)> submit_;
  IMPLEMENT_REFCOUNTING(Entry);
};

CefRefPtr<CefBoxLayout> Box(CefRefPtr<CefPanel> panel, bool vertical, int gap = 0) {
  CefBoxLayoutSettings settings;
  settings.horizontal = !vertical;
  settings.between_child_spacing = gap;
  return panel->SetToBoxLayout(settings);
}

void AddButton(CefRefPtr<CefPanel> parent, const std::string& text,
               std::function<void()> action) {
  auto button = CefLabelButton::CreateLabelButton(new Button(std::move(action)), text);
  button->SetHorizontalAlignment(CEF_HORIZONTAL_ALIGNMENT_LEFT);
  parent->AddChildView(button);
}

class PopupWindow : public CefWindowDelegate {
 public:
  PopupWindow(CefRefPtr<CefBrowserView> view, std::string title, bool address_bar = false)
      : view_(view), title_(std::move(title)), address_bar_(address_bar) {}
  void OnWindowCreated(CefRefPtr<CefWindow> window) override {
    window->SetTitle(title_);
    auto panel = CefPanel::CreatePanel(nullptr);
    auto layout = Box(panel, true, 4);
    window->AddChildView(panel);
    CefRefPtr<CefTextfield> field;
    if (address_bar_) {
      field = CefTextfield::CreateTextfield(new Entry([view = view_](std::string input) {
        if (auto page = view->GetBrowser()) {
          page->GetMainFrame()->LoadURL(Resolve(std::move(input)));
          view->RequestFocus();
        }
      }));
      field->SetPlaceholderText("Search or enter an address");
      field->SetAccessibleName("Address");
      panel->AddChildView(field);
    }
    panel->AddChildView(view_);
    layout->SetFlexForView(view_, 1);
    window->Show();
    if (field) field->RequestFocus();
    else view_->RequestFocus();
  }
  CefSize GetPreferredSize(CefRefPtr<CefView>) override { return {880, 640}; }
  bool CanClose(CefRefPtr<CefWindow>) override {
    auto browser = view_->GetBrowser();
    return !browser || browser->GetHost()->TryCloseBrowser();
  }
  void OnWindowDestroyed(CefRefPtr<CefWindow>) override { view_ = nullptr; }
 private:
  CefRefPtr<CefBrowserView> view_;
  const std::string title_;
  const bool address_bar_;
  IMPLEMENT_REFCOUNTING(PopupWindow);
};

class ViewDelegate : public CefBrowserViewDelegate {
 public:
  // CEF permits multiple Alloy views in one window. Chrome-style views are
  // limited to one per window, which cannot represent Cra's tabs and splits.
  cef_runtime_style_t GetBrowserRuntimeStyle() override { return CEF_RUNTIME_STYLE_ALLOY; }

  bool OnPopupBrowserViewCreated(CefRefPtr<CefBrowserView>,
                                 CefRefPtr<CefBrowserView> popup, bool) override {
    CefWindow::CreateTopLevelWindow(new PopupWindow(popup, "Cra Browser"));
    return true;
  }
  IMPLEMENT_REFCOUNTING(ViewDelegate);
};

class Shell;

class MainWindow : public CefWindowDelegate {
 public:
  explicit MainWindow(CefRefPtr<Shell> shell);
  void OnWindowCreated(CefRefPtr<CefWindow> window) override;
  bool CanClose(CefRefPtr<CefWindow> window) override;
  void OnWindowDestroyed(CefRefPtr<CefWindow> window) override;
  bool OnAccelerator(CefRefPtr<CefWindow>, int command) override;
  CefSize GetPreferredSize(CefRefPtr<CefView>) override { return {1220, 800}; }
 private:
  CefRefPtr<Shell> shell_;
  IMPLEMENT_REFCOUNTING(MainWindow);
};

class Shell : public CefClient,
              public CefLifeSpanHandler,
              public CefDisplayHandler,
              public CefDownloadHandler,
              public CefFocusHandler,
              public CefLoadHandler {
 public:
  Shell(const std::filesystem::path& path, const std::vector<std::string>& urls, bool smoke)
      : profile_path_(path), session_(path / "session.json"), smoke_(smoke) {
    writable_ = session_.Load();
    if (!writable_) std::cerr << "Cra could not read session.json. Keeping the original file.\n";
    session_.ArchiveToday(Session::Now() - 86400, session_.selected);
    for (const auto& url : urls) session_.Add(Resolve(url));
    if (smoke_) session_.Add("data:text/html,%3Ctitle%3ECra%20CEF%20smoke%3C/title%3E");
  }

  CefRefPtr<CefLifeSpanHandler> GetLifeSpanHandler() override { return this; }
  CefRefPtr<CefDisplayHandler> GetDisplayHandler() override { return this; }
  CefRefPtr<CefLoadHandler> GetLoadHandler() override { return this; }
  CefRefPtr<CefDownloadHandler> GetDownloadHandler() override { return this; }

  bool OnBeforeDownload(CefRefPtr<CefBrowser>, CefRefPtr<CefDownloadItem>,
                        const CefString& suggested_name,
                        CefRefPtr<CefBeforeDownloadCallback> callback) override {
    callback->Continue(std::filesystem::path(suggested_name.ToString()).filename().string(), true);
    return true;
  }
  CefRefPtr<CefFocusHandler> GetFocusHandler() override { return this; }

  void Relaunch(const std::vector<std::string>& urls) {
    if (closing_ || !window_) return;
    for (const auto& url : urls) session_.Add(Resolve(url));
    ShowSelected();
    window_->Activate();
  }

  void OnGotFocus(CefRefPtr<CefBrowser> browser) override {
    if (closing_ || !address_) return;
    if (secondary_ && secondary_->GetBrowser() == browser) {
      secondary_focused_ = true;
    } else if (auto* tab = FindBrowser(browser); tab && tab->id == session_.selected) {
      secondary_focused_ = false;
    } else {
      return;
    }
    address_->SetText(browser->GetMainFrame()->GetURL());
  }

  void Build(CefRefPtr<CefWindow> window) {
    window_ = window;
    window_->SetTitle("Cra Browser");
    auto root = CefPanel::CreatePanel(nullptr);
    auto row = Box(root, false, 8);
    window_->SetToFillLayout();
    window_->AddChildView(root);

    sidebar_ = CefPanel::CreatePanel(nullptr);
    Box(sidebar_, true, 4);
    sidebar_->SetSize({238, 0});
    root->AddChildView(sidebar_);

    auto workspace = CefPanel::CreatePanel(nullptr);
    auto column = Box(workspace, true, 4);
    root->AddChildView(workspace);
    row->SetFlexForView(workspace, 1);

    auto toolbar = CefPanel::CreatePanel(nullptr);
    auto bar = Box(toolbar, false, 4);
    workspace->AddChildView(toolbar);
    AddButton(toolbar, "Back", [this] { if (auto page = Active()) page->GoBack(); });
    AddButton(toolbar, "Forward", [this] { if (auto page = Active()) page->GoForward(); });
    AddButton(toolbar, "Reload", [this] { if (auto page = Active()) page->Reload(); });
    address_ = CefTextfield::CreateTextfield(new Entry([this](std::string input) {
      Navigate(std::move(input));
    }));
    address_->SetPlaceholderText("Search or enter an address");
    address_->SetAccessibleName("Address and command bar");
    toolbar->AddChildView(address_);
    bar->SetFlexForView(address_, 1);
    AddButton(toolbar, "Split", [this] { Accelerate('E'); });
    AddButton(toolbar, "DevTools", [this] {
      if (auto page = Active())
        page->GetHost()->ShowDevTools(CefWindowInfo{}, this, CefBrowserSettings{}, CefPoint{});
    });

    auto panes = CefPanel::CreatePanel(nullptr);
    auto split = Box(panes, false, 4);
    workspace->AddChildView(panes);
    column->SetFlexForView(panes, 1);
    left_ = CefPanel::CreatePanel(nullptr);
    left_->SetToFillLayout();
    right_ = CefPanel::CreatePanel(nullptr);
    right_->SetToFillLayout();
    panes->AddChildView(left_);
    panes->AddChildView(right_);
    split->SetFlexForView(left_, 1);
    split->SetFlexForView(right_, 1);
    right_->SetVisible(false);

    for (const int key : {'T', 'L', 'W', 'D', 'E', 'S'})
      window_->SetAccelerator(key, key, false, true, false, true);

    ShowSelected();
    window_->Show();
    window_->Layout();
  }

  bool Accelerate(int command) {
    switch (command) {
      case 'T': AddTab("about:blank"); [[fallthrough]];
      case 'L': address_->RequestFocus(); address_->SelectAll(false); return true;
      case 'W': CloseSelected(); return true;
      case 'D': PinSelected(); return true;
      case 'S': sidebar_->SetVisible(!sidebar_->IsVisible()); window_->Layout(); return true;
      case 'E': ToggleSplit(); return true;
      default: return false;
    }
  }

  bool CanClose() {
    if (closing_) return browsers_.empty();
    closing_ = true;
    Persist();
    const auto browsers = browsers_;
    for (const auto& [id, browser] : browsers) browser->GetHost()->CloseBrowser(true);
    return browsers_.empty();
  }

  void Destroyed() {
    window_ = nullptr;
    sidebar_ = nullptr;
    address_ = nullptr;
    left_ = nullptr;
    right_ = nullptr;
    views_.clear();
    secondary_ = nullptr;
    if (browsers_.empty()) CefQuitMessageLoop();
  }

  void OnAfterCreated(CefRefPtr<CefBrowser> browser) override {
    browsers_[browser->GetIdentifier()] = browser;
    if (closing_) browser->GetHost()->CloseBrowser(true);
  }

  void OnBeforeClose(CefRefPtr<CefBrowser> browser) override {
    browsers_.erase(browser->GetIdentifier());
    if (!closing_ || !browsers_.empty()) return;
    CefRefPtr<Shell> self(this);
    CefPostTask(TID_UI, new UiTask([shell = std::move(self)] {
      if (shell->window_) shell->window_->Close();
      else CefQuitMessageLoop();
    }));
  }

  void OnAddressChange(CefRefPtr<CefBrowser> browser, CefRefPtr<CefFrame> frame,
                       const CefString& url) override {
    if (closing_ || !frame->IsMain()) return;
    if (secondary_focused_ && secondary_ && secondary_->GetBrowser() == browser &&
        !address_->HasFocus()) address_->SetText(url);
    if (auto* tab = FindBrowser(browser)) {
      tab->url = url;
      if (tab->id == session_.selected && !secondary_focused_ && !address_->HasFocus())
        address_->SetText(url);
      Persist();
    }
  }

  void OnTitleChange(CefRefPtr<CefBrowser> browser, const CefString& title) override {
    if (closing_) return;
    if (auto* tab = FindBrowser(browser)) {
      tab->title = title;
      RefreshSidebar();
      Persist();
    }
  }

  void OnLoadEnd(CefRefPtr<CefBrowser>, CefRefPtr<CefFrame> frame, int) override {
    if (!smoke_ || smoke_done_ || !frame->IsMain() || !frame->GetURL().ToString().starts_with("data:text/html"))
      return;
    std::cout << "Cra CEF smoke test: Chromium loaded the local fixture." << std::endl;
    smoke_done_ = true;
    CefRefPtr<Shell> self(this);
    CefPostTask(TID_UI, new UiTask([shell = std::move(self)] {
      if (shell->window_) shell->window_->Close();
    }));
  }

 private:
  CefRefPtr<CefBrowser> Active() {
    if (secondary_focused_ && secondary_ && right_->IsVisible()) return secondary_->GetBrowser();
    return SelectedBrowser();
  }

  CefRefPtr<CefBrowser> SelectedBrowser() {
    const auto view = views_.find(session_.selected);
    return view == views_.end() ? nullptr : view->second->GetBrowser();
  }

  Tab* FindBrowser(CefRefPtr<CefBrowser> browser) {
    auto view = CefBrowserView::GetForBrowser(browser);
    for (const auto& [id, candidate] : views_)
      if (candidate == view) return session_.Find(id);
    return nullptr;
  }

  void Persist() {
    if (!smoke_ && writable_ && !session_.Save())
      std::cerr << "Cra could not save its session.\n";
  }

  void AddTab(std::string url) {
    session_.Add(std::move(url));
    ShowSelected();
  }

  CefRefPtr<CefRequestContext> Context() {
    const auto space = std::find(session_.spaces.begin(), session_.spaces.end(), session_.space);
    const auto index = std::distance(session_.spaces.begin(), space);
    if (index == 0) return CefRequestContext::GetGlobalContext();
    auto& context = contexts_[index];
    if (!context) {
      CefRequestContextSettings settings;
      CefString(&settings.cache_path) = (profile_path_ / ("Space-" + std::to_string(index))).string();
      settings.persist_session_cookies = true;
      context = CefRequestContext::CreateContext(settings, nullptr);
    }
    return context;
  }

  CefRefPtr<CefBrowserView> MakeView(const std::string& url, CefRefPtr<CefRequestContext> context) {
    return CefBrowserView::CreateBrowserView(this, url, CefBrowserSettings{},
                                             nullptr, context, new ViewDelegate());
  }

  void ResetSecondary() {
    if (secondary_) {
      auto page = secondary_->GetBrowser();
      right_->RemoveChildView(secondary_);
      secondary_ = nullptr;
      if (page) page->GetHost()->CloseBrowser(true);
    }
    secondary_focused_ = false;
    right_->SetVisible(false);
  }

  void ShowSelected() {
    secondary_focused_ = false;
    auto* tab = session_.Find(session_.selected);
    if (!tab) tab = &session_.Add("about:blank");
    const int id = tab->id;
    const std::string url = tab->url;
    tab->visited = Session::Now();
    for (const auto& [view_id, view] : views_) view->SetVisible(view_id == id);
    if (!views_.contains(id)) {
      auto view = MakeView(url, Context());
      views_[id] = view;
      left_->AddChildView(view);
    }
    address_->SetText(url == "about:blank" ? "" : url);
    views_.at(id)->RequestFocus();
    RefreshSidebar();
    Persist();
    window_->Layout();
  }

  void RefreshSidebar() {
    if (!sidebar_) return;
    sidebar_->RemoveAllChildViews();
    auto controls = CefPanel::CreatePanel(nullptr);
    Box(controls, true, 2);
    sidebar_->AddChildView(controls);
    AddButton(controls, "+ New tab", [this] { Accelerate('T'); });
    AddButton(controls, "Pin / unpin", [this] { PinSelected(); });
    AddButton(controls, archive_visible_ ? "Show tabs" : "Show archive", [this] {
      archive_visible_ = !archive_visible_;
      RefreshSidebar();
    });
    for (const auto& name : session_.spaces) {
      AddButton(controls, (name == session_.space ? "• " : "") + name, [this, name] {
        if (name != session_.space) ResetSecondary();
        session_.Switch(name);
        archive_visible_ = false;
        ShowSelected();
      });
    }
    auto scroll = CefScrollView::CreateScrollView(nullptr);
    auto list = CefPanel::CreatePanel(nullptr);
    Box(list, true, 1);
    size_t count = 0;
    const auto& tabs = archive_visible_ ? session_.archived : session_.tabs;
    for (const auto& tab : tabs) {
      if (tab.space != session_.space) continue;
      const auto name = tab.title.empty() ? tab.url : tab.title;
      const auto prefix = tab.favorite ? "★ " : (tab.home.empty() ? "" : "📌 ");
      const auto folder = tab.folder.empty() ? "" : tab.folder + " / ";
      AddButton(list, std::string(tab.id == session_.selected ? "› " : "") +
                      prefix + folder + name, [this, id = tab.id] {
        if (archive_visible_) {
          const auto found = std::find_if(session_.archived.begin(), session_.archived.end(),
                                         [id](const Tab& tab) { return tab.id == id; });
          if (found == session_.archived.end()) return;
          auto tab = *found;
          session_.archived.erase(found);
          auto& restored = session_.Add(tab.url);
          restored.title = tab.title;
          archive_visible_ = false;
        } else {
          session_.selected = id;
        }
        ShowSelected();
      });
      ++count;
    }
    list->SetSize({238, static_cast<int>(count * 36)});
    scroll->SetContentView(list);
    sidebar_->AddChildView(scroll);
    sidebar_->GetLayout()->AsBoxLayout()->SetFlexForView(scroll, 1);
    window_->Layout();
  }

  void Navigate(std::string input) {
    auto* tab = session_.Find(session_.selected);
    if (input.starts_with("/space ") && input.size() > 7) {
      if (input.substr(7) != session_.space) ResetSecondary();
      session_.Switch(input.substr(7));
      ShowSelected();
    } else if (tab && input.starts_with("/folder ") && input.size() > 8) {
      tab->folder = input.substr(8);
      if (tab->home.empty()) tab->home = tab->url;
      ShowSelected();
    } else if (tab && input == "/favorite") {
      tab->favorite = !tab->favorite;
      if (tab->favorite && tab->home.empty()) tab->home = tab->url;
      ShowSelected();
    } else if (tab && input == "/home" && !tab->home.empty()) {
      if (auto page = SelectedBrowser()) page->GetMainFrame()->LoadURL(tab->home);
    } else if (input == "/little") {
      CefWindow::CreateTopLevelWindow(new PopupWindow(
          MakeView(tab ? tab->url : "about:blank", Context()), "Little Cra", true));
      return;
    } else if (input == "/private") {
      auto context = CefRequestContext::CreateContext(CefRequestContextSettings{}, nullptr);
      CefWindow::CreateTopLevelWindow(new PopupWindow(
          MakeView("about:blank", context), "Cra Private Window", true));
      return;
    } else if (input.starts_with("/split ") && input.size() > 7) {
      const auto url = Resolve(input.substr(7));
      if (secondary_) {
        if (auto page = secondary_->GetBrowser()) page->GetMainFrame()->LoadURL(url);
      } else {
        secondary_ = MakeView(url, Context());
        right_->AddChildView(secondary_);
      }
      right_->SetVisible(true);
      window_->Layout();
      secondary_->RequestFocus();
      return;
    } else if (auto page = Active()) {
      page->GetMainFrame()->LoadURL(Resolve(std::move(input)));
    }
    if (auto page = Active()) page->GetHost()->SetFocus(true);
  }

  void CloseSelected() {
    if (secondary_focused_ && right_->IsVisible()) {
      ResetSecondary();
      ShowSelected();
      return;
    }
    const int id = session_.selected;
    auto page = SelectedBrowser();
    session_.Remove(id, true);
    if (const auto found = views_.find(id); found != views_.end()) {
      left_->RemoveChildView(found->second);
      views_.erase(found);
    }
    if (page) page->GetHost()->CloseBrowser(true);
    ShowSelected();
  }

  void PinSelected() {
    if (auto* tab = session_.Find(session_.selected)) {
      if (tab->home.empty()) tab->home = tab->url;
      else {
        tab->home.clear();
        tab->folder.clear();
        tab->favorite = false;
      }
      RefreshSidebar();
      Persist();
    }
  }

  void ToggleSplit() {
    if (!secondary_) {
      secondary_ = MakeView("about:blank", Context());
      right_->AddChildView(secondary_);
    }
    right_->SetVisible(!right_->IsVisible());
    if (right_->IsVisible()) secondary_->RequestFocus();
    else ShowSelected();
    window_->Layout();
  }

  const std::filesystem::path profile_path_;
  Session session_;
  const bool smoke_;
  bool smoke_done_ = false;
  bool writable_ = true;
  bool closing_ = false;
  bool archive_visible_ = false;
  bool secondary_focused_ = false;
  CefRefPtr<CefWindow> window_;
  CefRefPtr<CefPanel> sidebar_;
  CefRefPtr<CefPanel> left_;
  CefRefPtr<CefPanel> right_;
  CefRefPtr<CefTextfield> address_;
  CefRefPtr<CefBrowserView> secondary_;
  std::map<int, CefRefPtr<CefBrowserView>> views_;
  std::map<int, CefRefPtr<CefBrowser>> browsers_;
  std::map<long, CefRefPtr<CefRequestContext>> contexts_;
  IMPLEMENT_REFCOUNTING(Shell);
};

MainWindow::MainWindow(CefRefPtr<Shell> shell) : shell_(shell) {}
void MainWindow::OnWindowCreated(CefRefPtr<CefWindow> window) { shell_->Build(window); }
bool MainWindow::CanClose(CefRefPtr<CefWindow>) { return shell_->CanClose(); }
void MainWindow::OnWindowDestroyed(CefRefPtr<CefWindow>) { shell_->Destroyed(); }
bool MainWindow::OnAccelerator(CefRefPtr<CefWindow>, int command) {
  return shell_->Accelerate(command);
}

}  // namespace

CefRefPtr<CefClient> OpenBrowser(std::filesystem::path profile,
                                 const std::vector<std::string>& urls,
                                 bool smoke_test) {
  CefRefPtr<Shell> shell = new Shell(profile, urls, smoke_test);
  CefWindow::CreateTopLevelWindow(new MainWindow(shell));
  return shell;
}

void RelaunchBrowser(CefRefPtr<CefClient> client, const std::vector<std::string>& urls) {
  if (client) static_cast<Shell*>(client.get())->Relaunch(urls);
}
}  // namespace cra
