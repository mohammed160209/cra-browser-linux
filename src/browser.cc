#include "browser.h"

#include <algorithm>
#include <cctype>
#include <set>
#include <string_view>
#include <filesystem>
#include <functional>
#include <iostream>
#include <map>
#include <memory>
#include <string>
#include <utility>

#include "session.h"
#include "include/cef_app.h"
#include "include/cef_color_ids.h"
#include "include/cef_display_handler.h"
#include "include/cef_download_handler.h"
#include "include/cef_focus_handler.h"
#include "include/cef_image.h"
#include "include/cef_request_context.h"
#include "include/cef_life_span_handler.h"
#include "include/cef_load_handler.h"
#include "include/cef_menu_model.h"
#include "include/cef_menu_model_delegate.h"
#include "include/cef_parser.h"
#include "include/views/cef_box_layout.h"
#include "include/views/cef_fill_layout.h"
#include "include/views/cef_browser_view.h"
#include "include/views/cef_browser_view_delegate.h"
#include "include/views/cef_label_button.h"
#include "include/views/cef_overlay_controller.h"
#include "include/views/cef_panel_delegate.h"
#include "include/views/cef_scroll_view.h"
#include "include/views/cef_textfield.h"
#include "include/views/cef_textfield_delegate.h"
#include "include/views/cef_window.h"
#include "include/views/cef_window_delegate.h"
#include "include/cef_task.h"

namespace cra {
namespace {

constexpr int kSidebarWidth = 228;
constexpr cef_color_t kFrame = 0xffdbd8ed;
constexpr cef_color_t kSidebar = 0xffe5e0ef;
constexpr cef_color_t kInk = 0xff302b42;
constexpr cef_color_t kMuted = 0xff615a75;
constexpr cef_color_t kTile = 0xffd9d3e9;
constexpr cef_color_t kSelected = 0xfff8f6fb;
constexpr cef_color_t kToolbar = 0xff4348b9;
constexpr cef_color_t kToolbarInk = 0xfffaf9ff;
constexpr cef_color_t kCommand = 0xff231f30;
constexpr cef_color_t kCommandSelection = 0xff514b83;

std::string Label(const Tab& tab) {
  if (tab.url == "about:blank" || tab.url.empty()) return "New Tab";
  return tab.title.empty() ? tab.url : tab.title;
}

std::string DisplayAddress(const std::string& url) {
  if (url.empty() || url == "about:blank") return "Search or Enter URL…";
  CefURLParts parts;
  if (CefParseURL(url, parts)) {
    const auto host = CefString(&parts.host).ToString();
    if (!host.empty()) return host;
  }
  if (url.starts_with("file://"))
    return std::filesystem::path(url.substr(7)).filename().string();
  return url;
}

std::string Lowercase(std::string value) {
  for (char& c : value) c = static_cast<char>(std::tolower(static_cast<unsigned char>(c)));
  return value;
}

void ApplyChromeTheme(CefRefPtr<CefWindow> window) {
  window->SetThemeColor(CEF_ColorFrameActive, kFrame);
  window->SetThemeColor(CEF_ColorFrameInactive, kFrame);
  window->SetThemeColor(CEF_ColorTextfieldBackground, kCommand);
  window->SetThemeColor(CEF_ColorTextfieldForeground, kToolbarInk);
  window->SetThemeColor(CEF_ColorTextfieldForegroundPlaceholder, 0xffbbb4cd);
  window->SetThemeColor(CEF_ColorTextfieldSelectionBackground, kCommandSelection);
  window->SetThemeColor(CEF_ColorTextfieldSelectionForeground, kToolbarInk);
}

template <typename Delegate>
class PaintedView : public Delegate {
 public:
  explicit PaintedView(cef_color_t color, CefSize size = {}) : color_(color), size_(size) {}
  CefSize GetPreferredSize(CefRefPtr<CefView>) override { return size_; }
  CefSize GetMinimumSize(CefRefPtr<CefView>) override { return size_; }
  void OnThemeChanged(CefRefPtr<CefView> view) override { view->SetBackgroundColor(color_); }

 private:
  const cef_color_t color_;
  const CefSize size_;
  IMPLEMENT_REFCOUNTING(PaintedView);
};

CefRefPtr<CefPanel> Panel(cef_color_t color, CefSize size = {}) {
  return CefPanel::CreatePanel(new PaintedView<CefPanelDelegate>(color, size));
}

class SidebarViewport : public CefViewDelegate {
 public:
  void OnThemeChanged(CefRefPtr<CefView> view) override {
    view->SetBackgroundColor(kSidebar);
  }

  void OnLayoutChanged(CefRefPtr<CefView> view, const CefRect& bounds) override {
    const auto scroll = view->AsScrollView();
    const auto content = scroll->GetContentView();
    if (!content || bounds.width <= 0 || bounds.height <= 0) return;
    const int content_height = content->GetPreferredSize().height;
    const int scrollbar = content_height > bounds.height
        ? scroll->GetVerticalScrollbarWidth() : 0;
    const CefSize size(std::max(1, bounds.width - scrollbar),
                       std::max(bounds.height, content_height));
    if (content->GetSize() != size) content->SetSize(size);
  }

 private:
  IMPLEMENT_REFCOUNTING(SidebarViewport);
};

class UiTask : public CefTask {
 public:
  explicit UiTask(std::function<void()> action) : action_(std::move(action)) {}
  void Execute() override { action_(); }
 private:
  std::function<void()> action_;
  IMPLEMENT_REFCOUNTING(UiTask);
};

class FaviconDownload : public CefDownloadImageCallback {
 public:
  explicit FaviconDownload(std::function<void(CefRefPtr<CefImage>)> finished)
      : finished_(std::move(finished)) {}

  void OnDownloadImageFinished(const CefString&, int, CefRefPtr<CefImage> image) override {
    if (image && !image->IsEmpty()) finished_(image);
  }

 private:
  const std::function<void(CefRefPtr<CefImage>)> finished_;
  IMPLEMENT_REFCOUNTING(FaviconDownload);
};

class Button : public CefButtonDelegate {
 public:
  explicit Button(std::function<void()> action, cef_color_t background)
      : action_(std::move(action)), background_(background) {}
  void OnButtonPressed(CefRefPtr<CefButton>) override {
    auto action = action_;
    action();
  }
  void OnThemeChanged(CefRefPtr<CefView> view) override {
    if (background_) view->SetBackgroundColor(background_);
  }
 private:
  std::function<void()> action_;
  const cef_color_t background_;
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

class ViewButton : public CefButtonDelegate {
 public:
  ViewButton(std::function<void(CefRefPtr<CefButton>)> action, cef_color_t background)
      : action_(std::move(action)), background_(background) {}
  void OnButtonPressed(CefRefPtr<CefButton> button) override {
    auto action = action_;
    action(button);
  }
  void OnThemeChanged(CefRefPtr<CefView> view) override { view->SetBackgroundColor(background_); }
 private:
  const std::function<void(CefRefPtr<CefButton>)> action_;
  const cef_color_t background_;
  IMPLEMENT_REFCOUNTING(ViewButton);
};

CefRefPtr<CefLabelButton> AddMenuButton(
    CefRefPtr<CefPanel> parent, const std::string& title, const std::string& name,
    std::function<void(CefRefPtr<CefButton>)> action, int width = 28,
    cef_color_t background = kSidebar) {
  auto button = CefLabelButton::CreateLabelButton(new ViewButton(std::move(action), background),
                                                  title);
  button->SetFontList("sans-serif, 13px");
  button->SetEnabledTextColors(kInk);
  button->SetMinimumSize({width, 30});
  if (width) button->SetMaximumSize({width, 30});
  button->SetTooltipText(name);
  button->SetAccessibleName(name);
  parent->AddChildView(button);
  return button;
}

class CommandEntry : public CefTextfieldDelegate {
 public:
  CommandEntry(std::function<bool(int)> key, std::function<void()> changed)
      : key_(std::move(key)), changed_(std::move(changed)) {}

  bool OnKeyEvent(CefRefPtr<CefTextfield>, const CefKeyEvent& event) override {
    return event.type == KEYEVENT_RAWKEYDOWN && key_(event.windows_key_code);
  }

  void OnAfterUserAction(CefRefPtr<CefTextfield>) override { changed_(); }

 private:
  std::function<bool(int)> key_;
  std::function<void()> changed_;
  IMPLEMENT_REFCOUNTING(CommandEntry);
};

using MenuOptions = std::vector<std::pair<std::string, std::function<void()>>>;

class Menu : public CefMenuModelDelegate {
 public:
  explicit Menu(MenuOptions choices) : choices_(std::move(choices)) {}

  CefRefPtr<CefMenuModel> Model() {
    auto model = CefMenuModel::CreateMenuModel(this);
    for (size_t i = 0; i < choices_.size(); ++i)
      model->AddItem(static_cast<int>(i) + 1, choices_[i].first);
    return model;
  }

  void ExecuteCommand(CefRefPtr<CefMenuModel>, int id, cef_event_flags_t) override {
    if (id > 0 && static_cast<size_t>(id) <= choices_.size()) choices_[id - 1].second();
  }

 private:
  const MenuOptions choices_;
  IMPLEMENT_REFCOUNTING(Menu);
};

CefRefPtr<CefBoxLayout> Box(CefRefPtr<CefPanel> panel, bool vertical, int gap = 0,
                             CefInsets insets = {}) {
  CefBoxLayoutSettings settings;
  settings.horizontal = !vertical;
  settings.between_child_spacing = gap;
  settings.inside_border_insets = insets;
  return panel->SetToBoxLayout(settings);
}

CefRefPtr<CefLabelButton> AddButton(
    CefRefPtr<CefPanel> parent, const std::string& text,
    std::function<void()> action, cef_color_t foreground = kInk,
    cef_color_t background = kSidebar, int height = 30, bool center = false,
    int width = 0, std::string_view tooltip = {}, bool bold = false) {
  auto button = CefLabelButton::CreateLabelButton(new Button(std::move(action), background), text);
  button->SetFontList(bold ? "sans-serif, Bold 13px" : "sans-serif, 13px");
  button->SetHorizontalAlignment(center ? CEF_HORIZONTAL_ALIGNMENT_CENTER
                                        : CEF_HORIZONTAL_ALIGNMENT_LEFT);
  button->SetEnabledTextColors(foreground);
  button->SetInkDropEnabled(true);
  button->SetMinimumSize({width, height});
  if (width) button->SetMaximumSize({width, height});
  if (!tooltip.empty()) {
    button->SetTooltipText(std::string(tooltip));
    button->SetAccessibleName(std::string(tooltip));
  }
  parent->AddChildView(button);
  return button;
}

CefRefPtr<CefLabelButton> Caption(CefRefPtr<CefPanel> parent, const std::string& text,
                                  cef_color_t foreground = kMuted) {
  auto label = AddButton(parent, text, [] {}, foreground, kSidebar, 24, false, 0, {}, true);
  label->SetEnabled(false);
  label->SetTextColor(CEF_BUTTON_STATE_DISABLED, foreground);
  return label;
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

enum class CommandMode { NewTab, Address, Space, Folder };

enum ArchiveAccelerator {
  kRestoreClosed = 1000,
  kClearToday,
  kLittleWindow,
  kPrivateWindow,
};

class Shell;

class MainWindow : public CefWindowDelegate {
 public:
  explicit MainWindow(CefRefPtr<Shell> shell);
  void OnWindowCreated(CefRefPtr<CefWindow> window) override;
  bool CanClose(CefRefPtr<CefWindow> window) override;
  void OnWindowDestroyed(CefRefPtr<CefWindow> window) override;
  bool OnAccelerator(CefRefPtr<CefWindow>, int command) override;
  void OnWindowBoundsChanged(CefRefPtr<CefWindow>, const CefRect&) override;
  void OnThemeColorsChanged(CefRefPtr<CefWindow> window, bool) override {
    ApplyChromeTheme(window);
  }
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
    if (smoke_) session_.Add("data:text/html,%3Ctitle%3ECra%20CEF%20smoke%3C/title%3E#primary");
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
    if (closing_ || !location_) return;
    if (secondary_ && secondary_->GetBrowser() == browser) {
      secondary_focused_ = true;
    } else if (auto* tab = FindBrowser(browser); tab && tab->id == session_.selected) {
      secondary_focused_ = false;
    } else {
      return;
    }
    UpdateLocation(browser->GetMainFrame()->GetURL());
  }

  void Build(CefRefPtr<CefWindow> window) {
    window_ = window;
    window_->SetTitle("Cra");
    ApplyChromeTheme(window_);
    window_->ThemeChanged();
    auto root = Panel(kFrame);
    auto row = Box(root, false, 8, {8, 0, 8, 8});
    window_->SetToFillLayout();
    window_->AddChildView(root);

    sidebar_ = Panel(kSidebar, {kSidebarWidth, 1});
    Box(sidebar_, true, 6, {4, 8, 2, 8});
    root->AddChildView(sidebar_);

    auto workspace = Panel(kSelected);
    auto column = Box(workspace, true);
    root->AddChildView(workspace);
    row->SetFlexForView(workspace, 1);

    auto toolbar = Panel(kToolbar);
    auto bar = Box(toolbar, false, 3, {2, 6, 2, 6});
    workspace->AddChildView(toolbar);
    AddButton(toolbar, "◫", [this] { Accelerate('S'); },
              kToolbarInk, kToolbar, 29, true, 32, "Toggle sidebar");
    back_ = AddButton(toolbar, "←", [this] { if (auto page = Active()) page->GoBack(); },
                      kToolbarInk, kToolbar, 29, true, 30, "Back");
    forward_ = AddButton(toolbar, "→", [this] { if (auto page = Active()) page->GoForward(); },
                         kToolbarInk, kToolbar, 29, true, 30, "Forward");
    AddButton(toolbar, "↻", [this] { if (auto page = Active()) page->Reload(); },
              kToolbarInk, kToolbar, 29, true, 30, "Reload");
    location_ = AddButton(toolbar, "Search or Enter URL…",
                          [this] { OpenCommand(CommandMode::Address); },
                          kToolbarInk, kToolbar, 29, true, 0, "Open command bar");
    bar->SetFlexForView(location_, 1);
    back_->SetTextColor(CEF_BUTTON_STATE_DISABLED, 0xffabaee0);
    forward_->SetTextColor(CEF_BUTTON_STATE_DISABLED, 0xffabaee0);
    AddButton(toolbar, "◧", [this] { ToggleSplit(); },
              kToolbarInk, kToolbar, 29, true, 32, "Toggle Split View");

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

    BuildCommand();
    for (const int key : {'T', 'L', 'W', 'D', 'E', 'S'})
      window_->SetAccelerator(key, key, false, true, false, true);
    window_->SetAccelerator(kRestoreClosed, 'T', true, true, false, true);
    window_->SetAccelerator(kClearToday, 'K', true, true, false, true);
    window_->SetAccelerator(kLittleWindow, 'N', false, true, true, true);
    window_->SetAccelerator(kPrivateWindow, 'N', true, true, false, true);

    ShowSelected();
    window_->Show();
    window_->Layout();
    if (const auto* tab = session_.Find(session_.selected);
        tab && tab->url == "about:blank") OpenCommand(CommandMode::NewTab);
  }

  void PositionCommand() {
    if (!command_overlay_ || !command_overlay_->IsVisible()) return;
    const auto area = window_->GetClientAreaBoundsInScreen();
    const int width = std::clamp(area.width - 32, 1, 560);
    const int height = 58 + static_cast<int>(commands_.size()) * 34;
    command_overlay_->SetBounds({(area.width - width) / 2,
                                 std::max(8, area.height / 6), width, height});
  }

  bool Accelerate(int command) {
    switch (command) {
      case 'T': OpenCommand(CommandMode::NewTab); return true;
      case 'L': OpenCommand(CommandMode::Address); return true;
      case 'W': CloseSelected(); return true;
      case 'D': PinSelected(); return true;
      case 'S': sidebar_->SetVisible(!sidebar_->IsVisible()); window_->Layout(); return true;
      case 'E': ToggleSplit(); return true;
      case kRestoreClosed:
        if (!session_.archived.empty()) RestoreArchived(session_.archived.back().id);
        return true;
      case kClearToday: ClearToday(); return true;
      case kLittleWindow: Navigate("/little"); return true;
      case kPrivateWindow: Navigate("/private"); return true;
      default: return false;
    }
  }

  bool CanClose() {
    if (closing_) return true;
    closing_ = true;
    Persist();
    const auto browsers = browsers_;
    for (const auto& [id, browser] : browsers) browser->GetHost()->CloseBrowser(true);
    return true;
  }

  void Destroyed() {
    window_ = nullptr;
    sidebar_ = nullptr;
    location_ = nullptr;
    back_ = nullptr;
    forward_ = nullptr;
    command_overlay_ = nullptr;
    command_input_ = nullptr;
    command_results_ = nullptr;
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
    if (closing_ && !window_ && browsers_.empty()) CefQuitMessageLoop();
  }

  void OnAddressChange(CefRefPtr<CefBrowser> browser, CefRefPtr<CefFrame> frame,
                       const CefString& url) override {
    if (closing_ || !frame->IsMain()) return;
    if (secondary_focused_ && secondary_ && secondary_->GetBrowser() == browser)
      UpdateLocation(url);
    if (auto* tab = FindBrowser(browser)) {
      tab->url = url;
      if (tab->id == session_.selected && !secondary_focused_) UpdateLocation(url);
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

  void OnLoadingStateChange(CefRefPtr<CefBrowser> browser, bool, bool can_go_back,
                            bool can_go_forward) override {
    if (closing_ || !location_ || Active() != browser) return;
    back_->SetEnabled(can_go_back);
    forward_->SetEnabled(can_go_forward);
  }

  void OnFaviconURLChange(CefRefPtr<CefBrowser> browser,
                          const std::vector<CefString>& urls) override {
    if (closing_ || urls.empty()) return;
    const auto* tab = FindBrowser(browser);
    const auto url = urls.front().ToString();
    if (!tab || (!url.starts_with("https://") && !url.starts_with("http://"))) return;
    if (favicon_urls_[tab->id] == url) return;
    favicon_urls_[tab->id] = url;
    CefRefPtr<Shell> self(this);
    browser->GetHost()->DownloadImage(url, true, 32, false, new FaviconDownload(
        [self = std::move(self), id = tab->id, url](CefRefPtr<CefImage> image) {
          const auto requested = self->favicon_urls_.find(id);
          if (self->closing_ || !self->window_ || !self->session_.Find(id) ||
              requested == self->favicon_urls_.end() || requested->second != url) return;
          self->favicons_[id] = image;
          self->RefreshSidebar();
        }));
  }

  void OnLoadEnd(CefRefPtr<CefBrowser>, CefRefPtr<CefFrame> frame, int) override {
    if (!smoke_ || smoke_done_ || !frame->IsMain()) return;
    const auto url = frame->GetURL().ToString();
    if (!url.starts_with("data:text/html")) return;
    CefRefPtr<Shell> self(this);
    if (url.ends_with("#primary")) {
      CefPostTask(TID_UI, new UiTask([shell = std::move(self)] {
        if (!shell->window_ || shell->secondary_) return;
        shell->secondary_ = shell->MakeView(
            "data:text/html,%3Ctitle%3ECra%20second%20pane%3C/title%3E#secondary",
            shell->Context());
        shell->right_->AddChildView(shell->secondary_);
        shell->right_->SetVisible(true);
        shell->window_->Layout();
      }));
    } else if (url.ends_with("#secondary")) {
      std::cout << "Cra CEF smoke test: Chromium loaded local fixtures in both panes." << std::endl;
      smoke_done_ = true;
      CefPostTask(TID_UI, new UiTask([shell = std::move(self)] {
        if (shell->window_) shell->window_->Close();
      }));
    }
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
    CefBrowserSettings settings;
    settings.background_color = kSelected;
    return CefBrowserView::CreateBrowserView(this, url, settings, nullptr, context,
                                             new ViewDelegate());
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
    UpdateLocation(url);
    views_.at(id)->RequestFocus();
    RefreshSidebar();
    Persist();
    window_->Layout();
  }

  void UpdateLocation(const std::string& url) {
    location_->SetText(DisplayAddress(url));
    if (auto page = Active()) {
      back_->SetEnabled(page->CanGoBack());
      forward_->SetEnabled(page->CanGoForward());
    }
  }

  void ShowMenu(CefRefPtr<CefView> anchor, MenuOptions options) {
    CefRefPtr<Menu> menu = new Menu(std::move(options));
    const auto bounds = anchor->GetBoundsInScreen();
    window_->ShowMenu(menu->Model(), {bounds.x, bounds.y + bounds.height},
                      CEF_MENU_ANCHOR_TOPLEFT);
  }

  void SwitchSpace(const std::string& space) {
    if (space != session_.space) ResetSecondary();
    session_.Switch(space);
    archive_visible_ = false;
    ShowSelected();
  }

  void SelectTab(int id) {
    const auto* tab = session_.Find(id);
    if (!tab) return;
    if (tab->space != session_.space) {
      const auto space = tab->space;
      ResetSecondary();
      session_.Switch(space);
    }
    session_.selected = id;
    archive_visible_ = false;
    ShowSelected();
  }

  void TabMenu(CefRefPtr<CefView> anchor, int id) {
    const auto* tab = session_.Find(id);
    if (!tab) return;
    ShowMenu(anchor, {
        {tab->home.empty() ? "Pin Tab" : "Unpin Tab", [this, id] { TogglePin(id); }},
        {tab->favorite ? "Remove from Favorites" : "Add to Favorites",
         [this, id] { ToggleFavorite(id); }},
        {"Move to Folder…", [this, id] { OpenCommand(CommandMode::Folder, id); }},
        {"Open in Split View", [this, id] {
           if (const auto* item = session_.Find(id)) OpenSplit(item->url);
         }},
        {"Archive Tab", [this, id] { ArchiveTab(id); }},
    });
  }

  void AddTabRow(CefRefPtr<CefPanel> list, const Tab& tab, bool nested = false) {
    const bool active = !archive_visible_ && tab.id == session_.selected;
    auto row = active ? Panel(kSelected) : CefPanel::CreatePanel(nullptr);
    auto layout = Box(row, false, 1, {0, nested ? 13 : 0, 0, 0});
    const auto label = Label(tab);
    const auto icon = favicons_.find(tab.id);
    auto button = AddButton(row, icon == favicons_.end() ? "◦  " + label : label, [this, id = tab.id] {
      if (archive_visible_) RestoreArchived(id);
      else SelectTab(id);
    }, kInk, active ? kSelected : kSidebar, 31, false, 0, label);
    if (icon != favicons_.end()) button->SetImage(CEF_BUTTON_STATE_NORMAL, icon->second);
    layout->SetFlexForView(button, 1);
    if (!archive_visible_) {
      if (active)
        AddButton(row, "×", [this, id = tab.id] { ArchiveTab(id); },
                  kMuted, kSelected, 30, true, 24, "Close tab");
      AddMenuButton(row, "···", "Tab actions",
                    [this, id = tab.id](CefRefPtr<CefButton> anchor) { TabMenu(anchor, id); },
                    28, active ? kSelected : kSidebar);
    }
    list->AddChildView(row);
  }

  void RefreshSidebar() {
    if (!sidebar_) return;
    sidebar_->RemoveAllChildViews();
    auto header = CefPanel::CreatePanel(nullptr);
    auto header_layout = Box(header, false, 2);
    auto caption = Caption(header, archive_visible_ ? "Archive" : session_.space, kInk);
    header_layout->SetFlexForView(caption, 1);
    AddMenuButton(header, "···", "Cra menu", [this](CefRefPtr<CefButton> anchor) {
      ShowMenu(anchor, {
          {"New Space…", [this] { OpenCommand(CommandMode::Space); }},
          {"New Little Window", [this] { Navigate("/little"); }},
          {"New Private Window", [this] { Navigate("/private"); }},
          {"Developer Tools", [this] {
             if (auto page = Active())
               page->GetHost()->ShowDevTools(CefWindowInfo{}, this, CefBrowserSettings{}, CefPoint{});
           }},
      });
    });
    sidebar_->AddChildView(header);

    auto scroll = CefScrollView::CreateScrollView(new SidebarViewport);
    auto list = Panel(kSidebar);
    Box(list, true, 3);

    if (archive_visible_) {
      Caption(list, "Recently archived");
      bool any = false;
      for (auto it = session_.archived.rbegin(); it != session_.archived.rend(); ++it) {
        if (it->space != session_.space) continue;
        AddTabRow(list, *it);
        any = true;
      }
      if (!any) Caption(list, "Your archive is empty");
    } else {
      CefRefPtr<CefPanel> tiles;
      int tile_index = 0;
      for (const auto& tab : session_.tabs) {
        if (tab.space != session_.space || !tab.favorite) continue;
        if (tile_index++ % 4 == 0) {
          tiles = CefPanel::CreatePanel(nullptr);
          Box(tiles, false, 5);
          list->AddChildView(tiles);
        }
        const auto title = Label(tab);
        const auto glyph = !title.empty() && static_cast<unsigned char>(title.front()) < 128
            ? std::string(1, static_cast<char>(std::toupper(static_cast<unsigned char>(title.front()))))
            : "◦";
        const auto icon = favicons_.find(tab.id);
        auto tile = AddButton(tiles, icon == favicons_.end() ? glyph : "",
                              [this, id = tab.id] { SelectTab(id); },
                              kInk, tab.id == session_.selected ? kSelected : kTile,
                              44, true, 46, title, true);
        if (icon != favicons_.end()) tile->SetImage(CEF_BUTTON_STATE_NORMAL, icon->second);
      }

      std::set<std::string> shown_folders;
      bool pinned_heading = false;
      for (const auto& tab : session_.tabs) {
        if (tab.space != session_.space || tab.favorite || tab.home.empty()) continue;
        if (!pinned_heading) {
          Caption(list, "Pinned");
          pinned_heading = true;
        }
        if (tab.folder.empty()) {
          AddTabRow(list, tab);
          continue;
        }
        if (!shown_folders.insert(tab.folder).second) continue;
        const auto key = std::pair{tab.space, tab.folder};
        const bool collapsed = collapsed_folders_.contains(key);
        AddButton(list, (collapsed ? "›  " : "⌄  ") + tab.folder, [this, key] {
          if (!collapsed_folders_.erase(key)) collapsed_folders_.insert(key);
          RefreshSidebar();
        });
        if (!collapsed) {
          for (const auto& child : session_.tabs)
            if (child.space == key.first && child.folder == key.second &&
                !child.favorite && !child.home.empty()) AddTabRow(list, child, true);
        }
      }
      auto today = CefPanel::CreatePanel(nullptr);
      auto today_layout = Box(today, false);
      auto today_caption = Caption(today, "Today");
      today_layout->SetFlexForView(today_caption, 1);
      AddButton(today, "Clear", [this] { ClearToday(); }, kMuted, kSidebar, 24,
                true, 47, "Clear Today tabs");
      list->AddChildView(today);
      for (const auto& tab : session_.tabs)
        if (tab.space == session_.space && tab.home.empty() && !tab.favorite)
          AddTabRow(list, tab);
      AddButton(list, "+  New Tab", [this] { OpenCommand(CommandMode::NewTab); }, kMuted);
    }

    list->SetSize({kSidebarWidth - 16, list->GetPreferredSize().height});
    scroll->SetContentView(list);
    sidebar_->AddChildView(scroll);
    sidebar_->GetLayout()->AsBoxLayout()->SetFlexForView(scroll, 1);

    auto dock = Panel(kTile);
    auto dock_layout = Box(dock, false, 4, {1, 3, 1, 3});
    AddButton(dock, "▤", [this] {
      archive_visible_ = !archive_visible_;
      RefreshSidebar();
    }, kInk, archive_visible_ ? kSelected : kTile, 31, true, 32, "Toggle archive");
    auto spaces = AddMenuButton(dock, session_.space + "  ⌄", "Switch Space",
                                [this](CefRefPtr<CefButton> anchor) {
      MenuOptions options;
      for (const auto& space : session_.spaces)
        options.emplace_back(space, [this, space] { SwitchSpace(space); });
      ShowMenu(anchor, std::move(options));
    }, 0, kTile);
    dock_layout->SetFlexForView(spaces, 1);
    AddButton(dock, "+", [this] { OpenCommand(CommandMode::Space); },
              kInk, kTile, 31, true, 30, "Create a Space");
    sidebar_->AddChildView(dock);
    window_->Layout();
  }

  void BuildCommand() {
    auto panel = Panel(kCommand);
    auto layout = Box(panel, true, 4, {8, 10, 8, 10});
    command_input_ = CefTextfield::CreateTextfield(new CommandEntry(
        [this](int key) { return CommandKey(key); },
        [this] {
          if (command_input_->GetText().ToString() == command_query_) return;
          command_selection_ = 0;
          RefreshCommand();
        }));
    command_input_->SetFontList("sans-serif, 16px");
    command_input_->SetBackgroundColor(kCommand);
    command_input_->SetAccessibleName("Cra command bar");
    panel->AddChildView(command_input_);
    command_results_ = CefPanel::CreatePanel(nullptr);
    Box(command_results_, true, 2);
    panel->AddChildView(command_results_);
    layout->SetFlexForView(command_results_, 1);
    command_overlay_ = window_->AddOverlayView(panel, CEF_DOCKING_MODE_CUSTOM, true);
  }

  void OpenCommand(CommandMode mode, int tab = 0) {
    command_mode_ = mode;
    command_tab_ = tab;
    command_selection_ = 0;
    const char* placeholder = "Search or Enter URL…";
    std::string input;
    if (mode == CommandMode::Space) placeholder = "Name your new Space…";
    if (mode == CommandMode::Folder) {
      placeholder = "Enter a folder name…";
      if (const auto* item = session_.Find(tab)) input = item->folder;
    }
    if (mode == CommandMode::Address) {
      if (auto page = Active()) input = page->GetMainFrame()->GetURL();
      if (input == "about:blank") input.clear();
    }
    command_input_->SetPlaceholderText(placeholder);
    command_input_->SetText(input);
    command_overlay_->SetVisible(true);
    RefreshCommand();
    command_input_->RequestFocus();
    command_input_->SelectAll(false);
  }

  void RefreshCommand() {
    if (!command_overlay_->IsVisible()) return;
    command_results_->RemoveAllChildViews();
    commands_.clear();
    command_query_ = command_input_->GetText().ToString();
    const auto& input = command_query_;
    if (command_mode_ == CommandMode::Space || command_mode_ == CommandMode::Folder) {
      commands_.emplace_back(command_mode_ == CommandMode::Space ? "Create Space" : "Move tab",
                             [this, input] { Submit(input); });
    } else {
      if (!input.empty())
        commands_.emplace_back("↵  Open or search  ·  " + input,
                               [this, input] { Submit(input); });
      const auto query = Lowercase(input);
      auto append_matches = [&](const std::vector<Tab>& tabs, bool archived) {
        for (auto it = tabs.rbegin(); it != tabs.rend() && commands_.size() < 6; ++it) {
          if (it->url == "about:blank" || it->id == session_.selected) continue;
          if (!query.empty() && Lowercase(Label(*it)).find(query) == std::string::npos &&
              Lowercase(it->url).find(query) == std::string::npos) continue;
          const auto prefix = archived ? "Restore  ·  " : "Switch to  ·  ";
          commands_.emplace_back(prefix + Label(*it), [this, archived, id = it->id] {
            if (archived) RestoreArchived(id);
            else SelectTab(id);
          });
        }
      };
      append_matches(session_.tabs, false);
      if (!query.empty()) append_matches(session_.archived, true);
    }

    for (size_t i = 0; i < commands_.size(); ++i)
      AddButton(command_results_, commands_[i].first, [this, i] { RunCommand(i); },
                kToolbarInk, i == command_selection_ ? kCommandSelection : kCommand, 32);
    PositionCommand();
  }

  bool CommandKey(int key) {
    if (key == 27) {
      command_overlay_->SetVisible(false);
      if (auto page = Active()) page->GetHost()->SetFocus(true);
      return true;
    }
    if (key == 13) {
      if (commands_.empty()) Submit(command_input_->GetText().ToString());
      else RunCommand(command_selection_);
      return true;
    }
    if (key != 38 && key != 40) return false;
    if (commands_.empty()) return true;
    if (key == 38 && command_selection_ > 0) --command_selection_;
    if (key == 40 && command_selection_ + 1 < commands_.size()) ++command_selection_;
    RefreshCommand();
    return true;
  }

  void RunCommand(size_t index) {
    if (index >= commands_.size()) return;
    auto command = commands_[index].second;
    command_overlay_->SetVisible(false);
    command();
  }

  void Submit(const std::string& input) {
    command_overlay_->SetVisible(false);
    if (command_mode_ == CommandMode::Space) {
      if (!input.empty()) SwitchSpace(input);
    } else if (command_mode_ == CommandMode::Folder) {
      if (auto* tab = session_.Find(command_tab_); tab && !input.empty()) {
        tab->folder = input;
        tab->favorite = false;
        if (tab->home.empty()) tab->home = tab->url;
        RefreshSidebar();
        Persist();
      }
    } else if (command_mode_ == CommandMode::NewTab && !input.starts_with("/")) {
      const auto* tab = session_.Find(session_.selected);
      if (!tab || tab->url != "about:blank" || !tab->home.empty() || secondary_focused_)
        AddTab(Resolve(input));
      else Navigate(input);
    } else if (!input.empty()) {
      Navigate(input);
    }
    if (auto page = Active()) page->GetHost()->SetFocus(true);
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
      OpenSplit(Resolve(input.substr(7)));
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
    ArchiveTab(id);
  }

  void ArchiveTab(int id) {
    session_.Remove(id, true);
    DiscardTabView(id);
    ShowSelected();
  }

  void DiscardTabView(int id) {
    favicon_urls_.erase(id);
    favicons_.erase(id);
    const auto found = views_.find(id);
    if (found == views_.end()) return;
    auto page = found->second->GetBrowser();
    left_->RemoveChildView(found->second);
    views_.erase(found);
    if (page) page->GetHost()->CloseBrowser(true);
  }

  void RestoreArchived(int id) {
    const auto previous_space = session_.space;
    if (!session_.Restore(id)) return;
    if (session_.space != previous_space) ResetSecondary();
    archive_visible_ = false;
    ShowSelected();
  }

  void ClearToday() {
    const auto cleared = session_.ClearToday();
    if (cleared.empty()) return;
    for (const int id : cleared) DiscardTabView(id);
    ShowSelected();
  }

  void PinSelected() { TogglePin(session_.selected); }

  void TogglePin(int id) {
    if (auto* tab = session_.Find(id)) {
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

  void ToggleFavorite(int id) {
    if (auto* tab = session_.Find(id)) {
      tab->favorite = !tab->favorite;
      if (tab->favorite && tab->home.empty()) tab->home = tab->url;
      RefreshSidebar();
      Persist();
    }
  }

  void OpenSplit(const std::string& url) {
    if (secondary_) {
      if (auto page = secondary_->GetBrowser()) page->GetMainFrame()->LoadURL(url);
    } else {
      secondary_ = MakeView(url, Context());
      right_->AddChildView(secondary_);
    }
    right_->SetVisible(true);
    window_->Layout();
    secondary_->RequestFocus();
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
  CefRefPtr<CefLabelButton> location_;
  CefRefPtr<CefLabelButton> back_;
  CefRefPtr<CefLabelButton> forward_;
  CefRefPtr<CefTextfield> command_input_;
  CefRefPtr<CefPanel> command_results_;
  CefRefPtr<CefOverlayController> command_overlay_;
  CommandMode command_mode_ = CommandMode::Address;
  int command_tab_ = 0;
  size_t command_selection_ = 0;
  MenuOptions commands_;
  std::string command_query_;
  std::map<int, std::string> favicon_urls_;
  std::map<int, CefRefPtr<CefImage>> favicons_;
  std::set<std::pair<std::string, std::string>> collapsed_folders_;
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
void MainWindow::OnWindowBoundsChanged(CefRefPtr<CefWindow>, const CefRect&) {
  shell_->PositionCommand();
}

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
