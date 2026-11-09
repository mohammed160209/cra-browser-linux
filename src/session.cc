#include "session.h"

#include <algorithm>
#include <chrono>
#include <cstdio>
#include <fstream>
#include <iterator>
#include <system_error>

#include "include/cef_parser.h"

namespace cra {
namespace {

CefRefPtr<CefListValue> WriteTabs(const std::vector<Tab>& tabs) {
  auto list = CefListValue::Create();
  for (const auto& tab : tabs) {
    auto entry = CefDictionaryValue::Create();
    entry->SetInt("id", tab.id);
    entry->SetString("space", tab.space);
    entry->SetString("url", tab.url);
    entry->SetString("title", tab.title);
    entry->SetString("home", tab.home);
    entry->SetString("folder", tab.folder);
    entry->SetBool("favorite", tab.favorite);
    entry->SetDouble("visited", static_cast<double>(tab.visited));
    list->SetDictionary(list->GetSize(), entry);
  }
  return list;
}

std::vector<Tab> ReadTabs(CefRefPtr<CefListValue> list) {
  std::vector<Tab> result;
  if (!list) return result;
  for (size_t index = 0; index < list->GetSize(); ++index) {
    auto entry = list->GetDictionary(index);
    if (!entry || entry->GetInt("id") <= 0) continue;
    result.push_back({entry->GetInt("id"), entry->GetString("space"),
                      entry->GetString("url"), entry->GetString("title"),
                      entry->GetString("home"), entry->GetString("folder"),
                      entry->GetBool("favorite"),
                      static_cast<long long>(entry->GetDouble("visited"))});
  }
  return result;
}

}  // namespace

Session::Session(std::filesystem::path path) : path_(std::move(path)) {}

bool Session::Load() {
  std::ifstream input(path_);
  if (!input) return true;
  const std::string json((std::istreambuf_iterator<char>(input)), {});
  auto value = CefParseJSON(json, JSON_PARSER_RFC);
  if (!value || value->GetType() != VTYPE_DICTIONARY) return false;
  auto doc = value->GetDictionary();
  if (doc->GetInt("version") != 1) return false;

  if (auto names = doc->GetList("spaces"); names && names->GetSize()) {
    spaces.clear();
    for (size_t index = 0; index < names->GetSize(); ++index)
      spaces.push_back(names->GetString(index));
  }
  tabs = ReadTabs(doc->GetList("tabs"));
  archived = ReadTabs(doc->GetList("archive"));
  for (const auto& tab : tabs) next_id_ = std::max(next_id_, tab.id + 1);
  for (const auto& tab : archived) next_id_ = std::max(next_id_, tab.id + 1);
  Switch(doc->GetString("space"));
  if (const auto* tab = Find(doc->GetInt("selected")); tab && tab->space == space)
    selected = tab->id;
  return true;
}

bool Session::Save() const {
  auto doc = CefDictionaryValue::Create();
  doc->SetInt("version", 1);
  doc->SetString("space", space);
  doc->SetInt("selected", selected);
  auto names = CefListValue::Create();
  for (const auto& name : spaces) names->SetString(names->GetSize(), name);
  doc->SetList("spaces", names);
  doc->SetList("tabs", WriteTabs(tabs));
  doc->SetList("archive", WriteTabs(archived));
  auto value = CefValue::Create();
  value->SetDictionary(doc);

  auto temporary = path_;
  temporary += ".tmp";
  std::ofstream output(temporary, std::ios::trunc);
  output << CefWriteJSON(value, JSON_WRITER_PRETTY_PRINT).ToString();
  output.close();
  if (!output) return false;
  std::error_code error;
  std::filesystem::rename(temporary, path_, error);
  return !error;
}

Tab& Session::Add(std::string url) {
  tabs.push_back({next_id_++, space, std::move(url), {}, {}, {}, false, Now()});
  selected = tabs.back().id;
  return tabs.back();
}

Tab* Session::Find(int id) {
  const auto found = std::find_if(tabs.begin(), tabs.end(),
                                  [id](const Tab& tab) { return tab.id == id; });
  return found == tabs.end() ? nullptr : &*found;
}

void Session::Remove(int id, bool archive) {
  const auto found = std::find_if(tabs.begin(), tabs.end(),
                                  [id](const Tab& tab) { return tab.id == id; });
  if (found == tabs.end()) return;
  if (archive) archived.push_back(*found);
  const bool was_selected = selected == id;
  tabs.erase(found);
  if (was_selected) Switch(space);
}

void Session::Switch(std::string name) {
  if (name.empty()) name = spaces.front();
  if (std::find(spaces.begin(), spaces.end(), name) == spaces.end())
    spaces.push_back(name);
  space = std::move(name);
  selected = 0;
  long long last_visit = 0;
  for (const auto& tab : tabs) {
    if (tab.space == space && tab.visited >= last_visit) {
      selected = tab.id;
      last_visit = tab.visited;
    }
  }
}

void Session::ArchiveToday(long long cutoff, int protected_id) {
  std::vector<int> stale;
  for (const auto& tab : tabs) {
    if (tab.id != protected_id && tab.home.empty() && tab.visited < cutoff)
      stale.push_back(tab.id);
  }
  for (const int id : stale) Remove(id, true);
}

long long Session::Now() {
  return std::chrono::duration_cast<std::chrono::seconds>(
      std::chrono::system_clock::now().time_since_epoch()).count();
}

std::string Resolve(std::string input) {
  const auto first = input.find_first_not_of(" \t\r\n");
  if (first == std::string::npos) return "about:blank";
  input = input.substr(first, input.find_last_not_of(" \t\r\n") - first + 1);
  if (input.starts_with("https://") || input.starts_with("http://") ||
      input.starts_with("file://") || input.starts_with("chrome://") ||
      input == "about:blank")
    return input;
  const auto host = input.substr(0, input.find_first_of("/:"));
  if (input.find_first_of(" \t") == std::string::npos &&
      (host.find('.') != std::string::npos || host == "localhost"))
    return (host == "localhost" ? "http://" : "https://") + input;
  return "https://duckduckgo.com/?q=" + CefURIEncode(input, true).ToString();
}

}  // namespace cra
