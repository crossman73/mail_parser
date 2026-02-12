CREATE TABLE api_endpoints (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    path TEXT NOT NULL,
                    method TEXT NOT NULL,
                    summary TEXT,
                    description TEXT,
                    category TEXT,
                    version TEXT,
                    deprecated INTEGER DEFAULT 0,
                    auth_required INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                );

CREATE TABLE api_examples (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                endpoint_id INTEGER NOT NULL,
                language TEXT NOT NULL,
                title TEXT,
                request_code TEXT,
                response_code TEXT,
                FOREIGN KEY (endpoint_id) REFERENCES api_endpoints(id) ON DELETE CASCADE
            );

CREATE TABLE api_parameters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                endpoint_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                type TEXT,
                required INTEGER DEFAULT 0,
                location TEXT,
                description TEXT,
                default_value TEXT,
                example TEXT,
                FOREIGN KEY (endpoint_id) REFERENCES api_endpoints(id) ON DELETE CASCADE
            );

CREATE TABLE api_responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                endpoint_id INTEGER NOT NULL,
                status_code INTEGER NOT NULL,
                description TEXT,
                content_type TEXT DEFAULT 'application/json',
                schema TEXT,
                example TEXT,
                FOREIGN KEY (endpoint_id) REFERENCES api_endpoints(id) ON DELETE CASCADE
            );

CREATE TABLE api_test_executions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    endpoint_id INTEGER,
                    method TEXT,
                    status_code INTEGER,
                    response_time_ms INTEGER,
                    success INTEGER DEFAULT 1,
                    error_message TEXT,
                    request_data TEXT,
                    response_data TEXT,
                    executed_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    user_agent TEXT,
                    FOREIGN KEY (endpoint_id) REFERENCES api_endpoints(id) ON DELETE CASCADE
                );

CREATE TABLE chain_entry (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    evidence_id INTEGER,
                    file_path TEXT,
                    file_hash TEXT,
                    chain_hash TEXT,
                    FOREIGN KEY(evidence_id) REFERENCES evidence(id)
                );

CREATE TABLE evidence (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    evidence_number TEXT,
                    subject TEXT,
                    folder_path TEXT,
                    html_file TEXT,
                    pdf_file TEXT,
                    attachments_count INTEGER,
                    integrity_hash TEXT,
                    generated_at TEXT
                );

CREATE TABLE jobs (
                    id TEXT PRIMARY KEY,
                    status TEXT,
                    result TEXT,
                    created_at TEXT,
                    updated_at TEXT
                );

CREATE TABLE processed_emails (
                    id TEXT PRIMARY KEY,
                    file_id TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    process_time TEXT NOT NULL,
                    email_count INTEGER,
                    emails_data TEXT,  -- JSON 형태로 저장
                    evidence_generated INTEGER DEFAULT 0,
                    generated_evidence TEXT,  -- JSON 형태로 저장
                    deleted INTEGER DEFAULT 0,
                    deleted_at TEXT,
                    FOREIGN KEY (file_id) REFERENCES uploaded_files (id)
                );

CREATE TABLE processing_tasks (
                    id TEXT PRIMARY KEY,
                    task_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    progress REAL DEFAULT 0,
                    started_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    completed_at TEXT,
                    error_message TEXT
                );

CREATE TABLE schema_version (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        version INTEGER NOT NULL UNIQUE,
                        description TEXT,
                        applied_at TEXT DEFAULT CURRENT_TIMESTAMP
                    );

CREATE TABLE settings_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    setting_key TEXT NOT NULL,
                    old_value TEXT,
                    new_value TEXT,
                    changed_at TEXT NOT NULL,
                    changed_by TEXT DEFAULT 'system',
                    reason TEXT
                );

CREATE TABLE sqlite_sequence(name,seq);

CREATE TABLE system_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    level TEXT NOT NULL,
                    logger_name TEXT NOT NULL,
                    message TEXT NOT NULL,
                    module TEXT,
                    function TEXT,
                    line_no INTEGER,
                    thread_id INTEGER,
                    process_id INTEGER,
                    extra_data TEXT
                );

CREATE TABLE system_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    type TEXT NOT NULL DEFAULT 'string',
                    description TEXT,
                    category TEXT DEFAULT 'general',
                    is_sensitive INTEGER DEFAULT 0,
                    updated_at TEXT NOT NULL,
                    updated_by TEXT DEFAULT 'system'
                , created_at TEXT);

CREATE TABLE system_tests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    test_key TEXT UNIQUE NOT NULL,
                    test_name TEXT NOT NULL,
                    test_category TEXT NOT NULL,
                    test_description TEXT,
                    test_module TEXT NOT NULL,
                    test_function TEXT NOT NULL,
                    is_enabled INTEGER DEFAULT 1,
                    timeout_seconds INTEGER DEFAULT 30,
                    display_order INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

CREATE TABLE test_executions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    test_id INTEGER NOT NULL,
                    execution_time TEXT NOT NULL,
                    status TEXT NOT NULL,
                    result_message TEXT,
                    error_detail TEXT,
                    duration_ms INTEGER,
                    executed_by TEXT DEFAULT 'system',
                    FOREIGN KEY (test_id) REFERENCES system_tests (id)
                );

CREATE TABLE timeline_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timeline_id INTEGER NOT NULL,
                    event_type TEXT DEFAULT 'email',
                    timestamp TEXT NOT NULL,
                    title TEXT,
                    description TEXT,
                    email_id TEXT,
                    evidence_id INTEGER,
                    source_file TEXT,
                    attachments_json TEXT,
                    participants_json TEXT,
                    sort_order INTEGER DEFAULT 0,
                    is_key_event INTEGER DEFAULT 0,
                    legal_significance TEXT,
                    notes TEXT,
                    hash_value TEXT,
                    verified INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(timeline_id) REFERENCES timelines(id),
                    FOREIGN KEY(evidence_id) REFERENCES evidence(id)
                );

CREATE TABLE timelines (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    date_range_start TEXT,
                    date_range_end TEXT,
                    source_file TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    status TEXT DEFAULT 'draft',
                    hash TEXT
                );

CREATE TABLE uploaded_files (
                    id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    original_filename TEXT NOT NULL,
                    file_size INTEGER,
                    upload_time TEXT NOT NULL,
                    file_path TEXT,
                    status TEXT DEFAULT 'uploaded',
                    deleted INTEGER DEFAULT 0,
                    deleted_at TEXT,
                    deleted_reason TEXT
                );

CREATE INDEX idx_logs_level
                ON system_logs(level)
            ;

CREATE INDEX idx_logs_timestamp
                ON system_logs(timestamp DESC)
            ;

CREATE INDEX idx_timeline_events_timeline
                ON timeline_events(timeline_id)
            ;

CREATE INDEX idx_timeline_events_timestamp
                ON timeline_events(timestamp)
            ;

