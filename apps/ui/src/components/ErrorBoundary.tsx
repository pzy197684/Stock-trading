import React, { useCallback } from 'react';
import { Alert, AlertDescription, AlertTitle } from './ui/alert';
import { Button } from './ui/button';
import { RefreshCw, AlertTriangle, XCircle, Info } from 'lucide-react';
import type { ErrorBoundaryProps, ErrorInfo } from '../types/api';

interface ErrorBoundaryState {
  hasError: boolean;
  error?: Error;
  errorInfo?: React.ErrorInfo;
}

export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return {
      hasError: true,
      error
    };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('ErrorBoundary捕获到错误:', error, errorInfo);
    this.setState({
      error,
      errorInfo
    });

    // 可以在这里添加错误上报逻辑
    // reportError(error, errorInfo);
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: undefined, errorInfo: undefined });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return <this.props.fallback error={this.state.error!} retry={this.handleRetry} />;
      }

      return (
        <Alert variant="destructive" className="m-4">
          <AlertTriangle className="h-4 w-4" />
          <AlertTitle>组件错误</AlertTitle>
          <AlertDescription className="mt-2">
            <div className="mb-2">
              {this.state.error?.message || '组件渲染时发生未知错误'}
            </div>
            {process.env.NODE_ENV === 'development' && this.state.errorInfo && (
              <details className="mt-2 text-xs">
                <summary className="cursor-pointer">详细错误信息</summary>
                <pre className="mt-2 whitespace-pre-wrap">
                  {this.state.error?.stack}
                </pre>
              </details>
            )}
            <Button onClick={this.handleRetry} variant="outline" size="sm" className="mt-2">
              <RefreshCw className="h-4 w-4 mr-2" />
              重试
            </Button>
          </AlertDescription>
        </Alert>
      );
    }

    return this.props.children;
  }
}

// 错误处理Hook
export const useErrorHandler = () => {
  const handleError = useCallback((error: any, context: string): ErrorInfo => {
    console.error(`${context}错误:`, error);
    
    let errorMessage = '未知错误';
    let errorCode: string | undefined;
    
    if (error?.response?.data?.detail) {
      errorMessage = error.response.data.detail;
      errorCode = error.response?.status?.toString();
    } else if (error?.response?.data?.message) {
      errorMessage = error.response.data.message;
      errorCode = error.response?.status?.toString();
    } else if (error?.message) {
      errorMessage = error.message;
    } else if (typeof error === 'string') {
      errorMessage = error;
    }
    
    // 特定错误类型的友好提示
    if (errorMessage.includes('Network Error') || errorMessage.includes('Failed to fetch')) {
      errorMessage = '网络连接失败，请检查网络设置';
    } else if (errorMessage.includes('timeout')) {
      errorMessage = '请求超时，请稍后重试';
    } else if (errorMessage.includes('500')) {
      errorMessage = '服务器内部错误，请联系技术支持';
    } else if (errorMessage.includes('401')) {
      errorMessage = '身份验证失败，请重新登录';
    } else if (errorMessage.includes('403')) {
      errorMessage = '权限不足，无法执行此操作';
    } else if (errorMessage.includes('404')) {
      errorMessage = '请求的资源不存在';
    }
    
    return {
      title: `${context}失败`,
      message: errorMessage,
      timestamp: new Date().toISOString(),
      context,
      code: errorCode
    };
  }, []);
  
  return { handleError };
};

// 通用错误显示组件
interface ErrorDisplayProps {
  error: ErrorInfo | string | null;
  onRetry?: () => void;
  onDismiss?: () => void;
  variant?: 'default' | 'destructive';
  showDetails?: boolean;
}

export const ErrorDisplay: React.FC<ErrorDisplayProps> = ({
  error,
  onRetry,
  onDismiss,
  variant = 'destructive',
  showDetails = false
}) => {
  if (!error) return null;

  const errorInfo = typeof error === 'string' 
    ? { title: '错误', message: error, timestamp: new Date().toISOString() }
    : error;

  const getIcon = () => {
    switch (variant) {
      case 'destructive':
        return <XCircle className="h-4 w-4" />;
      default:
        return <Info className="h-4 w-4" />;
    }
  };

  return (
    <Alert variant={variant} className="mb-4">
      {getIcon()}
      <AlertTitle>{errorInfo.title}</AlertTitle>
      <AlertDescription>
        <div className="mb-2">{errorInfo.message}</div>
        
        {showDetails && errorInfo.code && (
          <div className="text-xs text-muted-foreground mb-2">
            错误代码: {errorInfo.code}
          </div>
        )}
        
        {showDetails && errorInfo.timestamp && (
          <div className="text-xs text-muted-foreground mb-2">
            时间: {new Date(errorInfo.timestamp).toLocaleString()}
          </div>
        )}
        
        <div className="flex gap-2">
          {onRetry && (
            <Button onClick={onRetry} variant="outline" size="sm">
              <RefreshCw className="h-4 w-4 mr-2" />
              重试
            </Button>
          )}
          {onDismiss && (
            <Button onClick={onDismiss} variant="ghost" size="sm">
              关闭
            </Button>
          )}
        </div>
      </AlertDescription>
    </Alert>
  );
};

// 加载状态组件
interface LoadingStateProps {
  message?: string;
  size?: 'sm' | 'md' | 'lg';
}

export const LoadingState: React.FC<LoadingStateProps> = ({ 
  message = '加载中...', 
  size = 'md' 
}) => {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-6 w-6', 
    lg: 'h-8 w-8'
  };

  return (
    <div className="flex items-center justify-center p-4">
      <div className="flex items-center gap-2">
        <RefreshCw className={`animate-spin ${sizeClasses[size]}`} />
        <span className="text-muted-foreground">{message}</span>
      </div>
    </div>
  );
};

// 空状态组件
interface EmptyStateProps {
  title: string;
  description?: string;
  action?: {
    label: string;
    onClick: () => void;
  };
  icon?: React.ReactNode;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title,
  description,
  action,
  icon
}) => {
  return (
    <div className="flex flex-col items-center justify-center p-8 text-center">
      {icon && <div className="mb-4 text-muted-foreground">{icon}</div>}
      <h3 className="text-lg font-semibold mb-2">{title}</h3>
      {description && (
        <p className="text-muted-foreground mb-4 max-w-sm">{description}</p>
      )}
      {action && (
        <Button onClick={action.onClick} variant="outline">
          {action.label}
        </Button>
      )}
    </div>
  );
};

// API状态检查组件
interface ApiStatusProps {
  isConnected: boolean;
  lastUpdate?: string;
  onReconnect?: () => void;
}

export const ApiStatus: React.FC<ApiStatusProps> = ({
  isConnected,
  lastUpdate,
  onReconnect
}) => {
  if (isConnected) {
    return (
      <div className="flex items-center gap-2 text-xs text-green-600">
        <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
        <span>API连接正常</span>
        {lastUpdate && (
          <span className="text-muted-foreground">
            · 更新于 {new Date(lastUpdate).toLocaleTimeString()}
          </span>
        )}
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2 text-xs text-red-600">
      <div className="w-2 h-2 bg-red-500 rounded-full" />
      <span>API连接断开</span>
      {onReconnect && (
        <Button onClick={onReconnect} variant="ghost" size="sm" className="h-6 px-2">
          重连
        </Button>
      )}
    </div>
  );
};