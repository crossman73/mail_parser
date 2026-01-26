Project_Rules:
  meta:
    project_name: mail_parser
    description: Court Evidence Management System - Flask web application for email evidence ingestion, parsing, and case management.
    primary_language: Python 3.13.9
    framework: Flask 3.1.2
    database: SQLite (data/db/email_parser.db)
    repository: github.com/crossman73/mail_parser
    current_branch: feature/admin-settings-clean
    default_branch: master
    last_updated: 2025-12-30

  purpose:
    - Provide mandatory rules and environment constraints for development and maintenance specific to mail_parser.
    - Ensure reproducibility, traceability, security, and Serena-compatible operational behavior.
    - Serve as canonical memory entry "Project_Rules" for Serena MCP.

  core_principles:
    - single-operator environment: all tasks must be automatable and maintainable by one operator.
    - automation-first: prioritize scripts/workflows that eliminate manual steps.
    - reproducibility: full environment must be rebuildable from version-controlled sources.
    - traceability: every action must produce logs/artifacts allowing audit and rollback.
    - honesty-over-assumption: unknowns must be flagged; never fabricate configuration or behavior.

  code_analysis_strategy:
    - symbol_level_analysis: ALWAYS prefer symbol-level analysis; avoid reading entire files.
    - use_serena_tools:
      - find_symbol
      - get_symbols_overview
      - find_referencing_symbols
      - grep_search (pattern matching across files)
      - search_for_pattern (when symbol names uncertain)
    - include_body_only_when_needed: set include_body=True only for focused inspection.
    - avoid_unnecessary_io: do not load large files unless required.

  memory_first_approach:
    - check_memories_before_start:
      - code_style_and_conventions
      - project_overview
      - recent_work_2025-12-30
      - serena_optimization_report
      - static_files_status
      - suggested_commands
      - task_completion_checklist
      - Project_Rules
    - reference_memories: read relevant memories to prevent redundant work and preserve consistency.

  mcp_tools_priority:
    - priority_order:
      - Serena MCP toolset
      - GitHub MCP integrations
      - Local tooling (grep, python)
    - prefer_serena_over_standard: when Serena tools available, use them first for discovery and modification.

  development_environment:
    - base_path: /volume1/docker/mail_parser
    - project_root: /volume1/docker/mail_parser (version-controllable canonical path)
    - python_version: 3.13.9
    - venv: .venv/ (located at project root)
    - package_manager: pip (use constraints.txt and infra/requirements.txt)
    - run_command: docker compose up -d (for containerized services where applicable)
    - required_files:
      - README.md
      - docker-compose.yml (if containerized)
      - .env (secure, excluded from repo)
    - required_directories:
      - src/
      - doc/
      - logs/
      - data/db/
      - data/cases/
      - data/timelines/
    - logging_rule:
      - format: "logs/yyMMddHHmmss_<project_name>.log"
      - requirement: every deployment, migration, or recovery action must produce a log file.

  key_dependencies:
    - Flask 3.1.2
    - SQLAlchemy
    - Jinja2
    - email parsing libs (mbox, mailparser)
    - see constraints.txt and infra/requirements.txt for exact pinned versions

  project_structure_snapshot:
    - src/web:
      - app.py: Flask application factory
      - routes.py: main route registry (939 lines)
      - blueprints:
        - main_routes.py (146 lines)
        - email_routes.py (152 lines)
        - evidence_routes.py (468 lines)
        - timeline_routes.py (151 lines)
        - integrity_routes.py (134 lines)
        - logs_routes.py (260 lines)
    - src/processing: email processing logic
    - src/models: database models
    - src/utils: utility functions
    - templates/: Jinja2 templates
    - static/:
      - css/modern-ui.css (dark mode support)
      - js/common.js
    - data/db/email_parser.db: SQLite database

  blueprint_architecture:
    - total_routes_registered: 94
    - blueprint_mappings:
      - /emails/*: email_routes.py
      - /evidence/*: evidence_routes.py
      - /timeline/*: timeline_routes.py
      - /integrity/*: integrity_routes.py
      - /logs/*: logs_routes.py
    - registration_point: src/web/app.py registers all blueprints
    - migration_notes:
      - duplicate /generate_evidence route removed
      - routes.py reduced from 1209 -> 939 lines

  coding_standards:
    - git_commit_format: 'YYYY-MM-DD HH:mm:ss_message'
      - example: git commit -m "2025-12-30 17:30:00_feat: Add new email parser function"
    - style_guides:
      - follow PEP 8
      - 4 spaces indentation (NO TABS)
      - max_line_length: 120
      - use type hints where applicable
      - docstrings for all public functions and classes
    - file_encoding: UTF-8 (must correctly handle Korean text)
    - ui_standards:
      - icons: Font Awesome only
      - responsive: Bootstrap-based
      - dark_mode_supported: modern-ui.css
      - accessibility: maintain ARIA labels and semantic HTML

  server_configuration:
    - development:
      - host: 0.0.0.0
      - port: 5000
      - debug: true (development only)
      - auto_reload: enabled
      - start_scripts:
        - server_start.bat
        - python src/runner/run_server.py
      - stop_scripts:
        - server_stop.bat
        - Ctrl+C
      - check_script: server_status.bat
    - environment_variables:
      - AUTO_KILL=1
      - FLASK_ENV=development
      - GITHUB_TOKEN (for GitHub MCP)
      - BRAVE_API_KEY (optional)
    - production_note:
      - never run debug mode in production
      - enforce secure session config and proper DB backups

  testing_standards:
    - after_route_change_mandatory_checks:
      - restart_server
      - verify_route_count == 94
      - test_affected_endpoints (GET/POST)
      - check_logs_for_errors
    - test_files:
      - unit_tests.py
      - integration_test.py
      - web_service_test.py
      - pytest.ini
    - scenario_testing: include realistic sample emails (with Korean content) and multiple-case flows

  performance_optimization:
    - code_efficiency:
      - avoid reading entire files; prefer symbol-level access
      - use pagination for large result sets
      - implement lazy loading for heavy pages
      - cache frequently accessed data
    - database:
      - use connection pooling where possible
      - add indexes for frequently queried columns
      - avoid N+1 queries (use eager loading where appropriate)
    - static_files:
      - minimize and bundle CSS/JS
      - enable browser caching and compression
      - compress images before commit

  security_guidelines:
    - input_validation:
      - sanitize all user inputs
      - validate file uploads: type, size, content (scan if required)
      - use parameterized queries / SQLAlchemy ORM
    - file_handling:
      - store uploaded files outside web root (data/cases/)
      - validate and canonicalize file paths to prevent traversal
      - enforce file size limits
    - authz_authn:
      - admin routes require authentication and role checks
      - use secure session management and CSRF protections
    - secrets_management:
      - sensitive_files: .env, claude.yaml, authorized_keys
      - never commit secrets to repo; use secret store or encrypted vault
      - rotate credentials on suspected exposure

  documentation_requirements:
    - README.md:
      - purpose, prerequisites, architecture summary, run & test steps, contact
    - doc/:
      - design notes, decisions, limitations, migration guides
    - code_docs:
      - docstrings for all functions/classes
      - inline comments for complex logic
    - memory_updates:
      - update Project_Rules memory when major changes occur

  debugging_and_logging:
    - logs_location: logs/
    - web_logs: logs/web_checks.json
    - debug_tools:
      - Flask debug toolbar (development only)
      - VS Code debugger configuration
      - Browser DevTools
    - incident_response:
      - document root cause in doc/incidents/
      - produce replayable steps and logs for audits

  prohibited_actions:
    - do_not_read_entire_source_unnecessarily
    - do_not_commit_sensitive_data (API keys, tokens, passwords)
    - do_not_hardcode_configuration_values
    - do_not_use_bootstrap_icons (migrated to Font Awesome)
    - do_not_create_files_without_integration_tests
    - do_not_make_bulk_changes_without_testing
    - do_not_commit_directly_to_master

  mandatory_operational_checks:
    - pre_action:
      - check required memories exist and are up-to-date
      - confirm branch (feature/* → target branch) before making changes
      - ensure .venv and dependency constraints aligned
    - post_action:
      - run unit and integration tests
      - verify route count and endpoints
      - produce log with standard naming format
      - update README or doc/ if behavior changed

  serena_behavior_rules:
    - obey_project_rules: Serena must enforce these rules when acting on behalf of the project.
    - explicit_requests: if required data is missing, Serena must request it explicitly.
    - no_fabrication: Serena must not invent configuration, commands, or facts.
    - symbol_first: Serena must use symbol-level tools before file-level reads.

  recent_changes:
    - phase: Phase 3 Complete (Blueprint Migration)
    - phase_latest: 3.7 (2025-12-30)
    - notable:
      - duplicate /generate_evidence route removed
      - removed 270 lines from routes.py (1209 -> 939)
      - total code reduction: 1967 -> 939 lines
      - commit_ref: e89a0ee

  required_memories:
    - code_style_and_conventions
    - project_overview
    - recent_work_2025-12-30
    - serena_optimization_report
    - static_files_status
    - suggested_commands
    - task_completion_checklist
    - Project_Rules

  contact_and_support:
    - repository: github.com/crossman73/mail_parser
    - owner: crossman73
    - branch_strategy: feature branches -> master
    - developer_tools:
      - IDE: VS Code
      - extensions: Python, GitHub Copilot, Serena MCP
      - terminal: PowerShell
      - os: Windows

  next_steps_recommendations:
    - create_serena_checklist: automated checklist that validates Project_Rules before merges
    - add_n8n_workflow: monitor for Project_Rules violations (tests failing, secrets in commits)
    - prepare_migration_docs: Phase 4 (Directory Restructuring) & Phase 5 (Documentation)