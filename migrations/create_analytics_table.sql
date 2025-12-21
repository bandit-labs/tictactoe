CREATE SCHEMA IF NOT EXISTS tictactoe;

-- Create game_analytics table
CREATE TABLE IF NOT EXISTS tictactoe.game_analytics (
    game_id VARCHAR PRIMARY KEY,
    player_x_id VARCHAR NOT NULL,
    player_o_id VARCHAR NOT NULL,
    player_x_name VARCHAR,
    player_o_name VARCHAR,
    mode VARCHAR NOT NULL,  -- 'pvp' or 'pvai'
    ai_difficulty VARCHAR,  -- 'easy', 'medium', 'hard'
    status VARCHAR NOT NULL,  -- 'in_progress', 'X_win', 'O_win', 'draw'
    move_count INTEGER DEFAULT 0 NOT NULL,
    created_at TIMESTAMP NOT NULL,
    finished_at TIMESTAMP
);

-- Create move_analytics table
CREATE TABLE IF NOT EXISTS tictactoe.move_analytics (
    id SERIAL PRIMARY KEY,
    game_id VARCHAR NOT NULL REFERENCES game_analytics(game_id) ON DELETE CASCADE,
    move_number INTEGER NOT NULL,
    player_id VARCHAR NOT NULL,
    mark VARCHAR NOT NULL,  -- 'X' or 'O'
    row INTEGER NOT NULL CHECK (row >= 0 AND row <= 2),
    col INTEGER NOT NULL CHECK (col >= 0 AND col <= 2),
    state_before JSONB NOT NULL,
    state_after JSONB NOT NULL,
    heuristic_value FLOAT NOT NULL DEFAULT 0.0,
    created_at TIMESTAMP NOT NULL,
    ai_metadata JSONB
);

-- Create indexes for performance
CREATE INDEX idx_game_analytics_status ON tictactoe.game_analytics(status);
CREATE INDEX idx_game_analytics_mode ON tictactoe.game_analytics(mode);
CREATE INDEX idx_game_analytics_created_at ON tictactoe.game_analytics(created_at);
CREATE INDEX idx_move_analytics_game_id ON tictactoe.move_analytics(game_id);
CREATE INDEX idx_move_analytics_move_number ON tictactoe.move_analytics(move_number);

-- Add comments
COMMENT ON TABLE tictactoe.game_analytics IS 'Analytics data for all games (including self-play) used for ML training';
COMMENT ON TABLE tictactoe.move_analytics IS 'Move-by-move analytics with state transitions and MCTS metadata';
COMMENT ON COLUMN tictactoe.move_analytics.state_before IS 'JSON: {"board": "XXO......", "next_player": "X"}';
COMMENT ON COLUMN tictactoe.move_analytics.state_after IS 'JSON: {"board": "XXOX.....", "next_player": "O"}';
COMMENT ON COLUMN tictactoe.move_analytics.ai_metadata IS 'JSON: MCTS stats (iterations, visits, wins, evaluation)';

-- Verify tables created
SELECT 'game_analytics' AS table_name, COUNT(*) AS row_count FROM tictactoe.game_analytics
UNION ALL
SELECT 'move_analytics', COUNT(*) FROM tictactoe.move_analytics;