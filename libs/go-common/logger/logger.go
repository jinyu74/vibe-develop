package logger

import (
	"io"
	"log/slog"
	"os"
	"strings"
)

type Config struct {
	Level  string `mapstructure:"level"`
	Format string `mapstructure:"format"`
	Output string `mapstructure:"output"`
}

func DefaultConfig() Config {
	return Config{
		Level:  "info",
		Format: "json",
		Output: "stdout",
	}
}

func New(cfg Config) *slog.Logger {
	level := parseLevel(cfg.Level)
	writer := parseOutput(cfg.Output)

	opts := &slog.HandlerOptions{
		Level:     level,
		AddSource: level == slog.LevelDebug,
	}

	var handler slog.Handler
	switch strings.ToLower(cfg.Format) {
	case "text":
		handler = slog.NewTextHandler(writer, opts)
	default:
		handler = slog.NewJSONHandler(writer, opts)
	}

	return slog.New(handler)
}

func parseLevel(s string) slog.Level {
	switch strings.ToLower(s) {
	case "debug":
		return slog.LevelDebug
	case "warn", "warning":
		return slog.LevelWarn
	case "error":
		return slog.LevelError
	default:
		return slog.LevelInfo
	}
}

func parseOutput(s string) io.Writer {
	switch strings.ToLower(s) {
	case "stderr":
		return os.Stderr
	default:
		return os.Stdout
	}
}
