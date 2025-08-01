-- Create finance schema
CREATE SCHEMA IF NOT EXISTS finance;

-- Expenses table (handles both recurring and one-time)
CREATE TABLE IF NOT EXISTS finance.expenses (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    amount DECIMAL(10,2) NOT NULL CHECK (amount > 0),
    currency VARCHAR(3) NOT NULL DEFAULT 'EUR',
    is_recurring BOOLEAN NOT NULL DEFAULT FALSE,
    
    -- For recurring expenses
    start_date DATE,
    end_date DATE,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- For one-time expenses  
    expense_date DATE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Revenue table
CREATE TABLE IF NOT EXISTS finance.revenue (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    amount DECIMAL(10,2) NOT NULL CHECK (amount > 0),
    currency VARCHAR(3) NOT NULL DEFAULT 'EUR',
    revenue_date DATE NOT NULL,
    external_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Simple indexes
CREATE INDEX IF NOT EXISTS idx_expenses_recurring ON finance.expenses(is_recurring, is_active);
CREATE INDEX IF NOT EXISTS idx_expenses_date ON finance.expenses(expense_date);
CREATE INDEX IF NOT EXISTS idx_expenses_start_date ON finance.expenses(start_date, end_date);
CREATE INDEX IF NOT EXISTS idx_revenue_date ON finance.revenue(revenue_date);

-- Add constraints to ensure data integrity
ALTER TABLE finance.expenses ADD CONSTRAINT check_recurring_dates 
    CHECK (
        (is_recurring = TRUE AND start_date IS NOT NULL AND expense_date IS NULL) OR
        (is_recurring = FALSE AND expense_date IS NOT NULL AND start_date IS NULL)
    );

ALTER TABLE finance.revenue
    ADD CONSTRAINT revenue_external_id_unique UNIQUE (external_id);

COMMENT ON TABLE finance.expenses IS 'All expenses - both recurring and one-time';
COMMENT ON TABLE finance.revenue IS 'All revenue entries including manual and API-sourced';
COMMENT ON COLUMN finance.expenses.is_recurring IS 'TRUE for monthly/yearly expenses, FALSE for one-time';
COMMENT ON COLUMN finance.expenses.is_active IS 'Only applies to recurring expenses - allows pause/resume';