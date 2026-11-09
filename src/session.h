#pragma once

#include <filesystem>
#include <string>
#include <vector>

namespace cra {

struct Tab {
  int id = 0;
  std::string space;
  std::string url;
  std::string title;
  std::string home;
  std::string folder;
  bool favorite = false;
  long long visited = 0;
};

class Session {
 public:
  explicit Session(std::filesystem::path path);

  bool Load();
  bool Save() const;
  Tab& Add(std::string url);
  Tab* Find(int id);
  void Remove(int id, bool archive);
  void Switch(std::string name);
  void ArchiveToday(long long cutoff, int protected_id = 0);
  static long long Now();

  std::vector<std::string> spaces{"Personal"};
  std::vector<Tab> tabs;
  std::vector<Tab> archived;
  std::string space = "Personal";
  int selected = 0;

 private:
  std::filesystem::path path_;
  int next_id_ = 1;
};

std::string Resolve(std::string input);

}  // namespace cra
