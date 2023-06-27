using System.Collections.Generic;

namespace OCRApp.Models;

public record struct OCRResults(Dictionary<string, string> Results);
