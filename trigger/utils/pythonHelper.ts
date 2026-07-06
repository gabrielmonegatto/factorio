import { execFile } from "child_process";
import { promisify } from "util";
import * as fs from "fs";

export const execFileAsync = promisify(execFile);

export function getPythonPath(): string {
  const paths = [
    "C:\\Users\\Monegatto\\AppData\\Local\\Programs\\Python\\Python310\\python.exe",
    "C:\\Users\\Monegatto\\AppData\\Local\\Programs\\Python\\Python311\\python.exe",
    "C:\\Users\\Monegatto\\AppData\\Local\\Programs\\Python\\Python312\\python.exe",
  ];
  for (const p of paths) {
    if (fs.existsSync(p)) {
      return p;
    }
  }
  return "python";
}
