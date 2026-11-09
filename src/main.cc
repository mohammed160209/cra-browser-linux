#include <cstdlib>
#include <filesystem>
#include <iostream>
#include <string>
#include <sys/stat.h>

#include "browser.h"
#include "include/cef_app.h"
#include "include/cef_command_line.h"

namespace {

class CraApp : public CefApp, public CefBrowserProcessHandler {
 public:
  explicit CraApp(std::filesystem::path profile) : profile_(std::move(profile)) {}

  CefRefPtr<CefBrowserProcessHandler> GetBrowserProcessHandler() override { return this; }

  void OnContextInitialized() override {
    auto command = CefCommandLine::GetGlobalCommandLine();
    std::vector<CefString> arguments;
    command->GetArguments(arguments);
    std::vector<std::string> urls(arguments.begin(), arguments.end());
    client_ = cra::OpenBrowser(profile_, urls, command->HasSwitch("cra-smoke-test"));
  }

  CefRefPtr<CefClient> GetDefaultClient() override { return client_; }

  bool OnAlreadyRunningAppRelaunch(CefRefPtr<CefCommandLine> command,
                                  const CefString&) override {
    std::vector<CefString> arguments;
    command->GetArguments(arguments);
    cra::RelaunchBrowser(client_, std::vector<std::string>(arguments.begin(), arguments.end()));
    return true;
  }

 private:
  const std::filesystem::path profile_;
  CefRefPtr<CefClient> client_;
  IMPLEMENT_REFCOUNTING(CraApp);
};

}  // namespace

int main(int argc, char** argv) {
  CefMainArgs args(argc, argv);
  const int child_exit = CefExecuteProcess(args, nullptr, nullptr);
  if (child_exit >= 0) return child_exit;

  umask(0077);
  std::filesystem::path root;
  if (const auto* data = std::getenv("XDG_DATA_HOME"); data && *data)
    root = data;
  else if (const auto* home = std::getenv("HOME"); home && *home)
    root = std::filesystem::path(home) / ".local/share";
  else {
    std::cerr << "Cra requires XDG_DATA_HOME or HOME.\n";
    return 1;
  }

  const auto profile = std::filesystem::absolute(root / "cra-browser-cef");
  std::error_code error;
  std::filesystem::create_directories(profile, error);
  if (error) {
    std::cerr << "Could not create Cra's profile directory: " << error.message() << '\n';
    return 1;
  }

  CefSettings settings;
  CefString(&settings.root_cache_path) = profile.string();
  CefString(&settings.cache_path) = (profile / "Default").string();
  CefString(&settings.log_file) = (profile / "chromium.log").string();
  settings.persist_session_cookies = true;
  settings.log_severity = LOGSEVERITY_WARNING;
  CefRefPtr<CraApp> app = new CraApp(profile);
  if (!CefInitialize(args, settings, app, nullptr))
    return CefGetExitCode();
  CefRunMessageLoop();
  app = nullptr;
  CefShutdown();
  return 0;
}
