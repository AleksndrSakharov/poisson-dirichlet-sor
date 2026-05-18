#pragma once

#include "models.hpp"

#include <string>

InputData parseInputJson(const std::string& path);
ProjectResult runProjectAnalysis(const InputData& input);
void writeResultJson(const std::string& outputPath, const ProjectResult& result);
void writeCsvTables(const std::string& outDir, const ProjectResult& result);
