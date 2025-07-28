-- Database initialization script for FastAPI Clean Architecture Template
-- This script is automatically executed when the PostgreSQL container starts

-- Create extensions if they don't exist
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Create schemas
CREATE SCHEMA IF NOT EXISTS public;
CREATE SCHEMA IF NOT EXISTS audit;
CREATE SCHEMA IF NOT EXISTS logs;

-- Set default search path
ALTER DATABASE fastapi_db SET search_path TO public, audit, logs;

-- Create audit table for tracking changes
CREATE TABLE IF NOT EXISTS audit.audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    table_name VARCHAR(255) NOT NULL,
    operation VARCHAR(10) NOT NULL CHECK (operation IN ('INSERT', 'UPDATE', 'DELETE')),
    old_values JSONB,
    new_values JSONB,
    user_id UUID,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ip_address INET,
    user_agent TEXT
);

-- Create indexes for audit table
CREATE INDEX IF NOT EXISTS idx_audit_log_table_name ON audit.audit_log(table_name);
CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit.audit_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_log_user_id ON audit.audit_log(user_id);

-- Create application logs table
CREATE TABLE IF NOT EXISTS logs.application_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    level VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    module VARCHAR(255),
    function_name VARCHAR(255),
    line_number INTEGER,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    extra_data JSONB,
    trace_id UUID,
    span_id VARCHAR(32),
    user_id UUID,
    request_id UUID
);

-- Create indexes for application logs
CREATE INDEX IF NOT EXISTS idx_app_logs_level ON logs.application_logs(level);
CREATE INDEX IF NOT EXISTS idx_app_logs_timestamp ON logs.application_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_app_logs_trace_id ON logs.application_logs(trace_id);
CREATE INDEX IF NOT EXISTS idx_app_logs_user_id ON logs.application_logs(user_id);

-- Create function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create audit trigger function
CREATE OR REPLACE FUNCTION audit_trigger_function()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        INSERT INTO audit.audit_log (table_name, operation, old_values, timestamp)
        VALUES (TG_TABLE_NAME, TG_OP, row_to_json(OLD), CURRENT_TIMESTAMP);
        RETURN OLD;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO audit.audit_log (table_name, operation, old_values, new_values, timestamp)
        VALUES (TG_TABLE_NAME, TG_OP, row_to_json(OLD), row_to_json(NEW), CURRENT_TIMESTAMP);
        RETURN NEW;
    ELSIF TG_OP = 'INSERT' THEN
        INSERT INTO audit.audit_log (table_name, operation, new_values, timestamp)
        VALUES (TG_TABLE_NAME, TG_OP, row_to_json(NEW), CURRENT_TIMESTAMP);
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Create base tables for the application

-- Authors table
CREATE TABLE IF NOT EXISTS authors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE,
    bio TEXT,
    birth_date DATE,
    nationality VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Create indexes for authors
CREATE INDEX IF NOT EXISTS idx_authors_name ON authors USING gin(name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_authors_email ON authors(email);
CREATE INDEX IF NOT EXISTS idx_authors_created_at ON authors(created_at);
CREATE INDEX IF NOT EXISTS idx_authors_is_active ON authors(is_active);

-- Create trigger for authors updated_at
DROP TRIGGER IF EXISTS update_authors_updated_at ON authors;
CREATE TRIGGER update_authors_updated_at
    BEFORE UPDATE ON authors
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create audit trigger for authors
DROP TRIGGER IF EXISTS authors_audit_trigger ON authors;
CREATE TRIGGER authors_audit_trigger
    AFTER INSERT OR UPDATE OR DELETE ON authors
    FOR EACH ROW
    EXECUTE FUNCTION audit_trigger_function();

-- Books table
CREATE TABLE IF NOT EXISTS books (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(500) NOT NULL,
    isbn VARCHAR(20) UNIQUE,
    author_id UUID NOT NULL REFERENCES authors(id) ON DELETE CASCADE,
    publication_date DATE,
    page_count INTEGER CHECK (page_count > 0),
    genre VARCHAR(100),
    description TEXT,
    price DECIMAL(10, 2) CHECK (price >= 0),
    stock_quantity INTEGER DEFAULT 0 CHECK (stock_quantity >= 0),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Create indexes for books
CREATE INDEX IF NOT EXISTS idx_books_title ON books USING gin(title gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_books_author_id ON books(author_id);
CREATE INDEX IF NOT EXISTS idx_books_isbn ON books(isbn);
CREATE INDEX IF NOT EXISTS idx_books_genre ON books(genre);
CREATE INDEX IF NOT EXISTS idx_books_publication_date ON books(publication_date);
CREATE INDEX IF NOT EXISTS idx_books_price ON books(price);
CREATE INDEX IF NOT EXISTS idx_books_created_at ON books(created_at);
CREATE INDEX IF NOT EXISTS idx_books_is_active ON books(is_active);

-- Create trigger for books updated_at
DROP TRIGGER IF EXISTS update_books_updated_at ON books;
CREATE TRIGGER update_books_updated_at
    BEFORE UPDATE ON books
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create audit trigger for books
DROP TRIGGER IF EXISTS books_audit_trigger ON books;
CREATE TRIGGER books_audit_trigger
    AFTER INSERT OR UPDATE OR DELETE ON books
    FOR EACH ROW
    EXECUTE FUNCTION audit_trigger_function();

-- Users table (for authentication and authorization)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    is_superuser BOOLEAN DEFAULT FALSE,
    last_login TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for users
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);

-- Create trigger for users updated_at
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create audit trigger for users (excluding password_hash from logs)
CREATE OR REPLACE FUNCTION users_audit_trigger_function()
RETURNS TRIGGER AS $$
DECLARE
    old_record JSONB;
    new_record JSONB;
BEGIN
    IF TG_OP = 'DELETE' THEN
        old_record := row_to_json(OLD)::JSONB;
        old_record := old_record - 'password_hash';
        INSERT INTO audit.audit_log (table_name, operation, old_values, timestamp)
        VALUES (TG_TABLE_NAME, TG_OP, old_record, CURRENT_TIMESTAMP);
        RETURN OLD;
    ELSIF TG_OP = 'UPDATE' THEN
        old_record := row_to_json(OLD)::JSONB;
        new_record := row_to_json(NEW)::JSONB;
        old_record := old_record - 'password_hash';
        new_record := new_record - 'password_hash';
        INSERT INTO audit.audit_log (table_name, operation, old_values, new_values, timestamp)
        VALUES (TG_TABLE_NAME, TG_OP, old_record, new_record, CURRENT_TIMESTAMP);
        RETURN NEW;
    ELSIF TG_OP = 'INSERT' THEN
        new_record := row_to_json(NEW)::JSONB;
        new_record := new_record - 'password_hash';
        INSERT INTO audit.audit_log (table_name, operation, new_values, timestamp)
        VALUES (TG_TABLE_NAME, TG_OP, new_record, CURRENT_TIMESTAMP);
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS users_audit_trigger ON users;
CREATE TRIGGER users_audit_trigger
    AFTER INSERT OR UPDATE OR DELETE ON users
    FOR EACH ROW
    EXECUTE FUNCTION users_audit_trigger_function();

-- Sessions table for user sessions
CREATE TABLE IF NOT EXISTS user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for sessions
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_token ON user_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON user_sessions(expires_at);

-- API Keys table for API authentication
CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    key_hash VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    scopes TEXT[] DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    expires_at TIMESTAMP WITH TIME ZONE,
    last_used TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for API keys
CREATE INDEX IF NOT EXISTS idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON api_keys(key_hash);
CREATE INDEX IF NOT EXISTS idx_api_keys_is_active ON api_keys(is_active);

-- Rate limiting table
CREATE TABLE IF NOT EXISTS rate_limits (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    identifier VARCHAR(255) NOT NULL, -- IP address, user ID, or API key
    endpoint VARCHAR(255) NOT NULL,
    requests_count INTEGER DEFAULT 0,
    window_start TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(identifier, endpoint, window_start)
);

-- Create indexes for rate limiting
CREATE INDEX IF NOT EXISTS idx_rate_limits_identifier ON rate_limits(identifier);
CREATE INDEX IF NOT EXISTS idx_rate_limits_endpoint ON rate_limits(endpoint);
CREATE INDEX IF NOT EXISTS idx_rate_limits_window_start ON rate_limits(window_start);

-- Task queue table for persistent task storage
CREATE TABLE IF NOT EXISTS task_queue (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id VARCHAR(255) UNIQUE NOT NULL,
    task_name VARCHAR(255) NOT NULL,
    task_args JSONB DEFAULT '{}',
    task_kwargs JSONB DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    priority INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    retry_count INTEGER DEFAULT 0,
    scheduled_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    result JSONB,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for task queue
CREATE INDEX IF NOT EXISTS idx_task_queue_task_id ON task_queue(task_id);
CREATE INDEX IF NOT EXISTS idx_task_queue_status ON task_queue(status);
CREATE INDEX IF NOT EXISTS idx_task_queue_scheduled_at ON task_queue(scheduled_at);
CREATE INDEX IF NOT EXISTS idx_task_queue_priority ON task_queue(priority DESC);

-- Create trigger for task_queue updated_at
DROP TRIGGER IF EXISTS update_task_queue_updated_at ON task_queue;
CREATE TRIGGER update_task_queue_updated_at
    BEFORE UPDATE ON task_queue
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Insert sample data (optional, for development)
DO $$
BEGIN
    -- Insert sample authors if they don't exist
    INSERT INTO authors (id, name, email, bio, nationality) VALUES
        ('550e8400-e29b-41d4-a716-446655440001', 'J.K. Rowling', 'jk.rowling@example.com', 'British author, best known for the Harry Potter series.', 'British'),
        ('550e8400-e29b-41d4-a716-446655440002', 'George Orwell', 'george.orwell@example.com', 'English novelist and essayist, journalist and critic.', 'British'),
        ('550e8400-e29b-41d4-a716-446655440003', 'Agatha Christie', 'agatha.christie@example.com', 'English writer known for her detective novels.', 'British')
    ON CONFLICT (id) DO NOTHING;

    -- Insert sample books if they don't exist
    INSERT INTO books (id, title, isbn, author_id, publication_date, page_count, genre, description, price, stock_quantity) VALUES
        ('660e8400-e29b-41d4-a716-446655440001', 'Harry Potter and the Philosopher''s Stone', '9780747532699', '550e8400-e29b-41d4-a716-446655440001', '1997-06-26', 223, 'Fantasy', 'The first book in the Harry Potter series.', 12.99, 100),
        ('660e8400-e29b-41d4-a716-446655440002', '1984', '9780451524935', '550e8400-e29b-41d4-a716-446655440002', '1949-06-08', 328, 'Dystopian Fiction', 'A dystopian social science fiction novel.', 13.99, 75),
        ('660e8400-e29b-41d4-a716-446655440003', 'Murder on the Orient Express', '9780062693662', '550e8400-e29b-41d4-a716-446655440003', '1934-01-01', 256, 'Mystery', 'A detective novel featuring Hercule Poirot.', 11.99, 50)
    ON CONFLICT (id) DO NOTHING;

    -- Insert a sample admin user (password: admin123)
    INSERT INTO users (id, email, username, password_hash, first_name, last_name, is_superuser, is_verified) VALUES
        ('770e8400-e29b-41d4-a716-446655440001', 'admin@example.com', 'admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3QJgusgqHu', 'Admin', 'User', true, true)
    ON CONFLICT (email) DO NOTHING;

EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'Sample data insertion failed: %', SQLERRM;
END $$;

-- Create views for common queries

-- Active books with author information
CREATE OR REPLACE VIEW active_books_with_authors AS
SELECT 
    b.id,
    b.title,
    b.isbn,
    b.publication_date,
    b.page_count,
    b.genre,
    b.description,
    b.price,
    b.stock_quantity,
    a.name as author_name,
    a.email as author_email,
    a.nationality as author_nationality,
    b.created_at,
    b.updated_at
FROM books b
JOIN authors a ON b.author_id = a.id
WHERE b.is_active = true AND a.is_active = true;

-- User statistics view
CREATE OR REPLACE VIEW user_statistics AS
SELECT 
    COUNT(*) as total_users,
    COUNT(*) FILTER (WHERE is_active = true) as active_users,
    COUNT(*) FILTER (WHERE is_verified = true) as verified_users,
    COUNT(*) FILTER (WHERE is_superuser = true) as admin_users,
    COUNT(*) FILTER (WHERE created_at >= CURRENT_DATE - INTERVAL '30 days') as new_users_last_30_days
FROM users;

-- Task queue statistics view
CREATE OR REPLACE VIEW task_queue_statistics AS
SELECT 
    status,
    COUNT(*) as count,
    AVG(EXTRACT(EPOCH FROM (completed_at - started_at))) as avg_duration_seconds
FROM task_queue
WHERE started_at IS NOT NULL
GROUP BY status;

-- Grant permissions
GRANT USAGE ON SCHEMA public TO fastapi_user;
GRANT USAGE ON SCHEMA audit TO fastapi_user;
GRANT USAGE ON SCHEMA logs TO fastapi_user;

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO fastapi_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA audit TO fastapi_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA logs TO fastapi_user;

GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO fastapi_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA audit TO fastapi_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA logs TO fastapi_user;

-- Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO fastapi_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA audit GRANT ALL ON TABLES TO fastapi_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA logs GRANT ALL ON TABLES TO fastapi_user;

ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO fastapi_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA audit GRANT ALL ON SEQUENCES TO fastapi_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA logs GRANT ALL ON SEQUENCES TO fastapi_user;

-- Create cleanup function for old logs and audit records
CREATE OR REPLACE FUNCTION cleanup_old_records()
RETURNS void AS $$
BEGIN
    -- Delete audit logs older than 1 year
    DELETE FROM audit.audit_log WHERE timestamp < CURRENT_TIMESTAMP - INTERVAL '1 year';
    
    -- Delete application logs older than 3 months
    DELETE FROM logs.application_logs WHERE timestamp < CURRENT_TIMESTAMP - INTERVAL '3 months';
    
    -- Delete expired sessions
    DELETE FROM user_sessions WHERE expires_at < CURRENT_TIMESTAMP;
    
    -- Delete completed tasks older than 1 month
    DELETE FROM task_queue WHERE status = 'completed' AND completed_at < CURRENT_TIMESTAMP - INTERVAL '1 month';
    
    -- Delete failed tasks older than 1 week (keep for debugging)
    DELETE FROM task_queue WHERE status = 'failed' AND created_at < CURRENT_TIMESTAMP - INTERVAL '1 week';
    
    RAISE NOTICE 'Cleanup completed at %', CURRENT_TIMESTAMP;
END;
$$ LANGUAGE plpgsql;

-- Log successful initialization
INSERT INTO logs.application_logs (level, message, module, timestamp)
VALUES ('INFO', 'Database initialization completed successfully', 'init-db.sql', CURRENT_TIMESTAMP);

