#pragma once

#include <filesystem>
#include <string>
#include <vector>

#include "include/cef_client.h"

namespace cra {
CefRefPtr<CefClient> OpenBrowser(std::filesystem::path profile,
                                 const std::vector<std::string>& urls,
                                 bool smoke_test);
void RelaunchBrowser(CefRefPtr<CefClient> client, const std::vector<std::string>& urls);
}  // namespace cra
