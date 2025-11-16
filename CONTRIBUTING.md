# Contributing

Thanks for your interest in improving this plugin! Here are some guidelines:

## Getting Started

1. Fork the repo.
2. Create a new branch for your feature/fix: `git checkout -b my-feature`
3. Make your changes.
4. Test by placing the plugin folder in `Packages/User` and reloading Sublime Text.

## Coding Guidelines

- Keep code modular (hover, completions, parsing logic separate).
- Use descriptive names for functions and variables.
- Avoid blocking the Sublime UI thread. Use caching when reading large files.
- Include comments for complex logic, especially regex parsing.

## Pull Requests

- Ensure your PR is targeted at `main`.
- Include a description of the changes and why they are needed.
- Test all features before submitting.