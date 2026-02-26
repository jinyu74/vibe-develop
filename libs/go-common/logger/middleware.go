package logger

import (
	"context"
	"log/slog"
)

type contextKey struct{}

func WithLogger(ctx context.Context, l *slog.Logger) context.Context {
	return context.WithValue(ctx, contextKey{}, l)
}

func FromContext(ctx context.Context) *slog.Logger {
	if l, ok := ctx.Value(contextKey{}).(*slog.Logger); ok {
		return l
	}
	return slog.Default()
}

func With(ctx context.Context, attrs ...slog.Attr) context.Context {
	l := FromContext(ctx)
	args := make([]any, len(attrs))
	for i, a := range attrs {
		args[i] = a
	}
	return WithLogger(ctx, l.With(args...))
}
