import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Link } from 'react-router-dom';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error,
      errorInfo: null,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    this.setState({
      error,
      errorInfo,
    });
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-gray-900 flex items-center justify-center px-4">
          <div className="max-w-2xl w-full">
            <div className="bg-gray-800 rounded-lg p-8 shadow-xl">
              <div className="flex items-center gap-4 mb-6">
                <div className="flex-shrink-0">
                  <svg
                    className="w-12 h-12 text-red-500"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                    />
                  </svg>
                </div>
                <div>
                  <h1 className="text-2xl font-bold text-white">
                    앗! 문제가 발생했습니다
                  </h1>
                  <p className="text-gray-400 mt-1">
                    예상치 못한 오류가 발생했습니다
                  </p>
                </div>
              </div>

              {process.env.NODE_ENV === 'development' && this.state.error && (
                <div className="mb-6">
                  <details className="bg-gray-900 rounded p-4">
                    <summary className="text-red-400 cursor-pointer font-medium mb-2">
                      오류 세부정보
                    </summary>
                    <div className="mt-2 text-sm">
                      <p className="text-red-300 font-mono mb-2">
                        {this.state.error.toString()}
                      </p>
                      {this.state.errorInfo && (
                        <pre className="text-gray-400 overflow-auto max-h-64 text-xs">
                          {this.state.errorInfo.componentStack}
                        </pre>
                      )}
                    </div>
                  </details>
                </div>
              )}

              <div className="flex gap-3">
                <button
                  onClick={this.handleReset}
                  className="px-6 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition-colors"
                >
                  다시 시도
                </button>
                <Link
                  to="/"
                  className="px-6 py-2 bg-gray-700 text-white rounded-md hover:bg-gray-600 transition-colors"
                >
                  홈으로 이동
                </Link>
                <button
                  onClick={() => window.location.reload()}
                  className="px-6 py-2 bg-gray-700 text-white rounded-md hover:bg-gray-600 transition-colors"
                >
                  페이지 새로고침
                </button>
              </div>

              <div className="mt-6 pt-6 border-t border-gray-700">
                <p className="text-sm text-gray-400">
                  문제가 계속되면 페이지를 새로고침하거나 관리자에게 문의하세요.
                </p>
              </div>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
