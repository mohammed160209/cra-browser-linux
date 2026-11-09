#include "session.h"

#include <filesystem>
#include <iostream>
#include <string>
#include <unistd.h>
#include "include/cef_api_hash.h"

int main() {
  if (!cef_api_hash(CEF_API_VERSION, 0)) return 7;
  auto path = std::filesystem::temp_directory_path() /
      ("cra-session-test-" + std::to_string(getpid()) + ".json");
  cra::Session original(path);
  const int personal = original.Add("https://example.org").id;
  original.Switch("Work");
  auto& pinned = original.Add("https://example.net");
  pinned.home = pinned.url;
  pinned.favorite = true;
  pinned.folder = "Research";
  const int work = pinned.id;
  const int closed = original.Add("https://example.com").id;
  original.Remove(closed, true);
  if (!original.Save()) return 1;

  cra::Session restored(path);
  if (!restored.Load()) return 2;
  std::filesystem::remove(path);
  const auto* tab = restored.Find(work);
  if (restored.space != "Work" || restored.selected != work ||
      restored.archived.size() != 1 || !tab || !tab->favorite ||
      tab->home != "https://example.net" || tab->folder != "Research" ||
      tab->visited == 0)
    return 3;
  restored.Switch("Personal");
  if (restored.selected != personal) return 4;
  if (restored.Restore(-1) || !restored.Restore(closed) || restored.space != "Work" ||
      restored.selected != closed || !restored.archived.empty())
    return 8;
  if (restored.ClearToday() != std::vector<int>{closed} || restored.Find(closed) ||
      !restored.Find(personal) || restored.selected != work)
    return 9;
  restored.Remove(work, true);
  if (!restored.Restore(work) || restored.Find(work)->folder != "Research" ||
      !restored.Find(work)->favorite || restored.Find(work)->home != "https://example.net")
    return 10;
  restored.ArchiveToday(cra::Session::Now() + 1);
  if (restored.tabs.size() != 1 || !restored.Find(work)) return 5;
  if (cra::Resolve(" example.org ") != "https://example.org" ||
      cra::Resolve("search words") != "https://duckduckgo.com/?q=search+words")
    return 6;
  std::cout << "Session, archive, and address resolution passed.\n";
}
