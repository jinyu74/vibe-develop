module.exports = {
  extends: ["@commitlint/config-conventional"],
  rules: {
    "type-enum": [
      2,
      "always",
      ["feat", "fix", "refactor", "docs", "test", "chore", "ci", "perf", "revert"],
    ],
    "scope-empty": [1, "never"],
    "subject-max-length": [2, "always", 72],
    "body-max-line-length": [1, "always", 120],
  },
};
