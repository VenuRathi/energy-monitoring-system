import { Component, type ErrorInfo, type ReactNode } from "react";

type AppErrorBoundaryProps = {
  children: ReactNode;
};

type AppErrorBoundaryState = {
  hasError: boolean;
};

export class AppErrorBoundary extends Component<AppErrorBoundaryProps, AppErrorBoundaryState> {
  state: AppErrorBoundaryState = {
    hasError: false,
  };

  static getDerivedStateFromError(): AppErrorBoundaryState {
    return { hasError: true };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("Dashboard render error", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="page-state page-state--error page-state--padded">
          <h3>Something went wrong while rendering the UI.</h3>
          <p>The page did not load correctly, but the app is still running. Refresh to try again.</p>
          <button type="button" className="ghost-button" onClick={() => window.location.reload()}>
            Reload page
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
