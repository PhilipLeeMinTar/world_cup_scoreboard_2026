# TTAstra 最佳实践

## 项目结构最佳实践

### 推荐目录结构
```
src/
├── routes/                    # 页面路由（约定式路由）
│   ├── layout.tsx            # 根布局
│   ├── page.tsx              # 首页
│   ├── dashboard/
│   │   ├── layout.tsx        # 仪表盘布局
│   │   ├── page.tsx          # 仪表盘首页
│   │   └── analytics/
│   │       └── page.tsx      # 分析页面
│   └── projects/
│       ├── layout.tsx        # 项目布局
│       ├── page.tsx          # 项目列表
│       └── [id]/
│           └── page.tsx      # 项目详情
├── components/               # 通用组件
│   ├── ui/                   # 基础 UI 组件
│   │   ├── Button/
│   │   │   ├── index.tsx
│   │   │   ├── Button.module.css
│   │   │   └── Button.test.tsx
│   │   └── Input/
│   ├── layout/               # 布局组件
│   │   ├── Header/
│   │   ├── Sidebar/
│   │   └── Footer/
│   └── business/             # 业务组件
│       ├── UserCard/
│       └── ProjectList/
├── pages/                    # 页面组件（配置式路由）
│   ├── Home/
│   ├── Dashboard/
│   └── Projects/
├── api/                      # BFF API
│   ├── users.ts
│   ├── projects.ts
│   └── auth/
│       └── login.ts
├── hooks/                    # 自定义 Hooks
│   ├── useAuth.ts
│   ├── useProjects.ts
│   └── useLocalStorage.ts
├── utils/                    # 工具函数
│   ├── api.ts
│   ├── format.ts
│   └── validation.ts
├── types/                    # 类型定义
│   ├── api.ts
│   ├── user.ts
│   └── project.ts
├── constants/                # 常量
│   ├── routes.ts
│   ├── api.ts
│   └── config.ts
├── styles/                   # 全局样式
│   ├── globals.css
│   ├── variables.css
│   └── reset.css
├── assets/                   # 静态资源
│   ├── images/
│   ├── icons/
│   └── fonts/
├── App.tsx                   # 应用入口（配置式路由）
└── entry.ts                  # 运行时入口
```

### 文件命名规范
- **组件文件**：PascalCase，如 `UserCard.tsx`
- **工具文件**：camelCase，如 `formatDate.ts`
- **常量文件**：UPPER_SNAKE_CASE，如 `API_ENDPOINTS.ts`
- **类型文件**：camelCase，如 `userTypes.ts`
- **样式文件**：kebab-case，如 `user-card.module.css`

## 组件开发最佳实践

### 1. 组件设计原则

#### 单一职责原则
```typescript
// ❌ 不好的设计
function UserDashboard({ user, projects, analytics }) {
  return (
    <div>
      <UserProfile user={user} />
      <ProjectList projects={projects} />
      <AnalyticsChart analytics={analytics} />
    </div>
  );
}

// ✅ 好的设计
function UserDashboard({ user, projects, analytics }) {
  return (
    <div>
      <UserProfile user={user} />
      <ProjectSection projects={projects} />
      <AnalyticsSection analytics={analytics} />
    </div>
  );
}

function ProjectSection({ projects }) {
  return (
    <section>
      <h2>Projects</h2>
      <ProjectList projects={projects} />
    </section>
  );
}
```

#### 组合优于继承
```typescript
// ✅ 使用组合模式
function Card({ children, className, ...props }) {
  return (
    <div className={`card ${className}`} {...props}>
      {children}
    </div>
  );
}

function CardHeader({ children }) {
  return <div className="card-header">{children}</div>;
}

function CardBody({ children }) {
  return <div className="card-body">{children}</div>;
}

// 使用
<Card>
  <CardHeader>Title</CardHeader>
  <CardBody>Content</CardBody>
</Card>
```

### 2. TypeScript 类型安全

#### 严格的类型定义
```typescript
// ✅ 完整的类型定义
interface User {
  id: string;
  name: string;
  email: string;
  avatar?: string;
  createdAt: Date;
  updatedAt: Date;
}

interface UserCardProps {
  user: User;
  onEdit?: (user: User) => void;
  onDelete?: (userId: string) => void;
  className?: string;
}

function UserCard({ user, onEdit, onDelete, className }: UserCardProps) {
  return (
    <div className={`user-card ${className}`}>
      <img src={user.avatar} alt={user.name} />
      <h3>{user.name}</h3>
      <p>{user.email}</p>
      {onEdit && <button onClick={() => onEdit(user)}>Edit</button>}
      {onDelete && <button onClick={() => onDelete(user.id)}>Delete</button>}
    </div>
  );
}
```

#### 泛型组件
```typescript
interface ListProps<T> {
  items: T[];
  renderItem: (item: T, index: number) => React.ReactNode;
  keyExtractor: (item: T) => string;
  className?: string;
}

function List<T>({ items, renderItem, keyExtractor, className }: ListProps<T>) {
  return (
    <div className={className}>
      {items.map((item, index) => (
        <div key={keyExtractor(item)}>
          {renderItem(item, index)}
        </div>
      ))}
    </div>
  );
}

// 使用
<List
  items={users}
  renderItem={(user) => <UserCard user={user} />}
  keyExtractor={(user) => user.id}
/>
```

### 3. 性能优化

#### React.memo 优化
```typescript
interface ExpensiveComponentProps {
  data: ComplexData;
  onUpdate: (data: ComplexData) => void;
}

const ExpensiveComponent = React.memo<ExpensiveComponentProps>(({ data, onUpdate }) => {
  // 复杂的计算逻辑
  const processedData = useMemo(() => {
    return processComplexData(data);
  }, [data]);

  return <div>{/* 渲染逻辑 */}</div>;
});

// 自定义比较函数
const UserCard = React.memo<UserCardProps>(({ user, onEdit }) => {
  return (
    <div>
      <h3>{user.name}</h3>
      <button onClick={() => onEdit(user)}>Edit</button>
    </div>
  );
}, (prevProps, nextProps) => {
  // 只有当用户 ID 改变时才重新渲染
  return prevProps.user.id === nextProps.user.id;
});
```

#### 懒加载组件
```typescript
import { lazy, Suspense } from 'react';

const LazyDashboard = lazy(() => import('./pages/Dashboard'));
const LazyAnalytics = lazy(() => import('./pages/Analytics'));

function App() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <Routes>
        <Route path="/dashboard" element={<LazyDashboard />} />
        <Route path="/analytics" element={<LazyAnalytics />} />
      </Routes>
    </Suspense>
  );
}
```

## 状态管理最佳实践

### 1. 状态分层

#### 本地状态
```typescript
function UserForm() {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
  });
  
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  // 本地状态管理逻辑
  return <form>{/* 表单内容 */}</form>;
}
```

#### 全局状态
```typescript
import { create } from 'zustand';

interface AppState {
  user: User | null;
  theme: 'light' | 'dark';
  language: string;
  setUser: (user: User | null) => void;
  setTheme: (theme: 'light' | 'dark') => void;
  setLanguage: (language: string) => void;
}

export const useAppStore = create<AppState>((set) => ({
  user: null,
  theme: 'light',
  language: 'en',
  setUser: (user) => set({ user }),
  setTheme: (theme) => set({ theme }),
  setLanguage: (language) => set({ language }),
}));
```

### 2. 自定义 Hooks

#### 数据获取 Hook
```typescript
interface UseApiOptions<T> {
  url: string;
  dependencies?: any[];
  enabled?: boolean;
}

function useApi<T>({ url, dependencies = [], enabled = true }: UseApiOptions<T>) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    if (!enabled) return;

    const fetchData = async () => {
      setLoading(true);
      setError(null);
      
      try {
        const response = await fetch(url);
        if (!response.ok) throw new Error('Failed to fetch');
        const result = await response.json();
        setData(result);
      } catch (err) {
        setError(err as Error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [url, enabled, ...dependencies]);

  return { data, loading, error, refetch: () => fetchData() };
}

// 使用
function UserList() {
  const { data: users, loading, error } = useApi<User[]>({
    url: '/api/users',
  });

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;
  
  return (
    <div>
      {users?.map(user => <UserCard key={user.id} user={user} />)}
    </div>
  );
}
```

#### 表单管理 Hook
```typescript
interface UseFormOptions<T> {
  initialValues: T;
  validation?: (values: T) => Record<string, string>;
  onSubmit: (values: T) => Promise<void>;
}

function useForm<T>({ initialValues, validation, onSubmit }: UseFormOptions<T>) {
  const [values, setValues] = useState<T>(initialValues);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleChange = (name: keyof T, value: any) => {
    setValues(prev => ({ ...prev, [name]: value }));
    // 清除对应字段的错误
    if (errors[name as string]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // 验证
    if (validation) {
      const validationErrors = validation(values);
      if (Object.keys(validationErrors).length > 0) {
        setErrors(validationErrors);
        return;
      }
    }

    setIsSubmitting(true);
    try {
      await onSubmit(values);
    } catch (error) {
      console.error('Form submission error:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return {
    values,
    errors,
    isSubmitting,
    handleChange,
    handleSubmit,
    setValues,
    setErrors,
  };
}
```

## 路由最佳实践

### 1. 路由配置管理

#### 路由常量
```typescript
// constants/routes.ts
export const ROUTES = {
  HOME: '/',
  DASHBOARD: '/dashboard',
  PROJECTS: '/projects',
  PROJECT_DETAIL: (id: string) => `/projects/${id}`,
  ANALYTICS: '/analytics',
  SETTINGS: '/settings',
} as const;

export type RouteKey = keyof typeof ROUTES;
```

#### 路由守卫
```typescript
// components/ProtectedRoute.tsx
interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredPermissions?: string[];
}

function ProtectedRoute({ children, requiredPermissions = [] }: ProtectedRouteProps) {
  const { user, isLoggedIn } = useByteCloudJwt();
  const navigate = useNavigate();

  useEffect(() => {
    if (!isLoggedIn) {
      navigate('/login');
      return;
    }

    if (requiredPermissions.length > 0 && user) {
      const hasPermission = requiredPermissions.every(permission => 
        user.permissions?.includes(permission)
      );
      
      if (!hasPermission) {
        navigate('/unauthorized');
        return;
      }
    }
  }, [isLoggedIn, user, requiredPermissions, navigate]);

  if (!isLoggedIn) return null;
  
  return <>{children}</>;
}

// 使用
<Route 
  path="/admin" 
  element={
    <ProtectedRoute requiredPermissions={['admin']}>
      <AdminPanel />
    </ProtectedRoute>
  } 
/>
```

### 2. 动态路由

#### 路由懒加载
```typescript
// utils/lazyRoute.ts
export function lazyRoute(importFn: () => Promise<{ default: React.ComponentType }>) {
  const LazyComponent = lazy(importFn);
  
  return function LazyRoute(props: any) {
    return (
      <Suspense fallback={<RouteLoading />}>
        <LazyComponent {...props} />
      </Suspense>
    );
  };
}

// 使用
const Dashboard = lazyRoute(() => import('./pages/Dashboard'));
const Analytics = lazyRoute(() => import('./pages/Analytics'));
```

## API 设计最佳实践

### 1. API 客户端封装

#### 基础 API 客户端
```typescript
// utils/api.ts
class ApiClient {
  private baseURL: string;
  private defaultHeaders: Record<string, string>;

  constructor(baseURL: string) {
    this.baseURL = baseURL;
    this.defaultHeaders = {
      'Content-Type': 'application/json',
    };
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    const config: RequestInit = {
      ...options,
      headers: {
        ...this.defaultHeaders,
        ...options.headers,
      },
    };

    const response = await fetch(url, config);
    
    if (!response.ok) {
      throw new ApiError(response.status, response.statusText);
    }

    return response.json();
  }

  async get<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'GET' });
  }

  async post<T>(endpoint: string, data: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async put<T>(endpoint: string, data: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'DELETE' });
  }
}

export const apiClient = new ApiClient('/api');
```

#### 类型安全的 API
```typescript
// types/api.ts
interface ApiResponse<T> {
  data: T;
  message: string;
  success: boolean;
}

interface User {
  id: string;
  name: string;
  email: string;
}

// API 方法
export const userApi = {
  getUsers: (): Promise<ApiResponse<User[]>> => 
    apiClient.get('/users'),
  
  getUser: (id: string): Promise<ApiResponse<User>> => 
    apiClient.get(`/users/${id}`),
  
  createUser: (user: Omit<User, 'id'>): Promise<ApiResponse<User>> => 
    apiClient.post('/users', user),
  
  updateUser: (id: string, user: Partial<User>): Promise<ApiResponse<User>> => 
    apiClient.put(`/users/${id}`, user),
  
  deleteUser: (id: string): Promise<ApiResponse<void>> => 
    apiClient.delete(`/users/${id}`),
};
```

### 2. 错误处理

#### 统一错误处理
```typescript
// utils/errorHandler.ts
export class ApiError extends Error {
  constructor(
    public status: number,
    public statusText: string,
    message?: string
  ) {
    super(message || `API Error: ${status} ${statusText}`);
    this.name = 'ApiError';
  }
}

export function handleApiError(error: unknown): string {
  if (error instanceof ApiError) {
    switch (error.status) {
      case 401:
        return '未授权，请重新登录';
      case 403:
        return '权限不足';
      case 404:
        return '资源不存在';
      case 500:
        return '服务器内部错误';
      default:
        return `请求失败: ${error.statusText}`;
    }
  }
  
  if (error instanceof Error) {
    return error.message;
  }
  
  return '未知错误';
}
```

## 性能优化最佳实践

### 1. 代码分割

#### 路由级别分割
```typescript
// 使用 React.lazy 进行路由分割
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Analytics = lazy(() => import('./pages/Analytics'));
const Settings = lazy(() => import('./pages/Settings'));

function App() {
  return (
    <Router>
      <Suspense fallback={<PageLoading />}>
        <Routes>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </Suspense>
    </Router>
  );
}
```

#### 组件级别分割
```typescript
// 大型组件分割
const HeavyChart = lazy(() => import('./components/HeavyChart'));
const DataTable = lazy(() => import('./components/DataTable'));

function Dashboard() {
  const [showChart, setShowChart] = useState(false);
  
  return (
    <div>
      <button onClick={() => setShowChart(!showChart)}>
        Toggle Chart
      </button>
      
      {showChart && (
        <Suspense fallback={<div>Loading chart...</div>}>
          <HeavyChart />
        </Suspense>
      )}
    </div>
  );
}
```

### 2. 内存优化

#### 清理副作用
```typescript
function useWebSocket(url: string) {
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    const ws = new WebSocket(url);
    setSocket(ws);

    ws.onmessage = (event) => {
      setMessage(event.data);
    };

    // 清理函数
    return () => {
      ws.close();
    };
  }, [url]);

  return { socket, message };
}
```

#### 避免内存泄漏
```typescript
function useInterval(callback: () => void, delay: number | null) {
  const savedCallback = useRef(callback);

  useEffect(() => {
    savedCallback.current = callback;
  }, [callback]);

  useEffect(() => {
    if (delay === null) return;

    const id = setInterval(() => savedCallback.current(), delay);
    return () => clearInterval(id);
  }, [delay]);
}
```

## 测试最佳实践

### 1. 单元测试

#### 组件测试
```typescript
// components/__tests__/UserCard.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { UserCard } from '../UserCard';

describe('UserCard', () => {
  const mockUser = {
    id: '1',
    name: 'John Doe',
    email: 'john@example.com',
    avatar: 'avatar.jpg',
  };

  it('renders user information', () => {
    render(<UserCard user={mockUser} />);
    
    expect(screen.getByText('John Doe')).toBeInTheDocument();
    expect(screen.getByText('john@example.com')).toBeInTheDocument();
  });

  it('calls onEdit when edit button is clicked', () => {
    const onEdit = jest.fn();
    render(<UserCard user={mockUser} onEdit={onEdit} />);
    
    fireEvent.click(screen.getByText('Edit'));
    expect(onEdit).toHaveBeenCalledWith(mockUser);
  });

  it('calls onDelete when delete button is clicked', () => {
    const onDelete = jest.fn();
    render(<UserCard user={mockUser} onDelete={onDelete} />);
    
    fireEvent.click(screen.getByText('Delete'));
    expect(onDelete).toHaveBeenCalledWith('1');
  });
});
```

#### Hook 测试
```typescript
// hooks/__tests__/useApi.test.ts
import { renderHook, waitFor } from '@testing-library/react';
import { useApi } from '../useApi';

// Mock fetch
global.fetch = jest.fn();

describe('useApi', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('fetches data successfully', async () => {
    const mockData = { id: 1, name: 'Test' };
    (fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockData,
    });

    const { result } = renderHook(() => useApi({ url: '/api/test' }));

    await waitFor(() => {
      expect(result.current.data).toEqual(mockData);
      expect(result.current.loading).toBe(false);
      expect(result.current.error).toBeNull();
    });
  });

  it('handles fetch error', async () => {
    (fetch as jest.Mock).mockRejectedValueOnce(new Error('Fetch failed'));

    const { result } = renderHook(() => useApi({ url: '/api/test' }));

    await waitFor(() => {
      expect(result.current.data).toBeNull();
      expect(result.current.loading).toBe(false);
      expect(result.current.error).toBeInstanceOf(Error);
    });
  });
});
```

### 2. 集成测试

#### 页面测试
```typescript
// pages/__tests__/Dashboard.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { Dashboard } from '../Dashboard';

// Mock API
jest.mock('../../utils/api', () => ({
  userApi: {
    getUsers: jest.fn().mockResolvedValue({
      data: [
        { id: '1', name: 'John Doe', email: 'john@example.com' },
        { id: '2', name: 'Jane Smith', email: 'jane@example.com' },
      ],
    }),
  },
}));

describe('Dashboard', () => {
  it('renders user list', async () => {
    render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
      expect(screen.getByText('Jane Smith')).toBeInTheDocument();
    });
  });
});
```

## 部署最佳实践

### 1. 环境配置

#### 环境变量管理
```typescript
// config/env.ts
interface EnvConfig {
  NODE_ENV: 'development' | 'production' | 'test';
  API_BASE_URL: string;
  CDN_BASE_URL: string;
  ENABLE_ANALYTICS: boolean;
}

export const env: EnvConfig = {
  NODE_ENV: process.env.NODE_ENV as any,
  API_BASE_URL: process.env.REACT_APP_API_BASE_URL || '/api',
  CDN_BASE_URL: process.env.REACT_APP_CDN_BASE_URL || '',
  ENABLE_ANALYTICS: process.env.REACT_APP_ENABLE_ANALYTICS === 'true',
};
```

#### 多环境配置
```typescript
// solution.config.ts
export default defineConfig({
  deploy: {
    vgeos: ['row', 'eu', 'us'],
    domains: ['www.tiktok.com'],
  },
  capabilities: {
    slardar: {
      bid: process.env.REACT_APP_SLARDAR_BID || 'default-bid',
    },
  },
});
```

### 2. 构建优化

#### 构建配置优化
```typescript
// solution.config.ts
export default defineConfig({
  edenx: {
    output: {
      // 代码分割配置
      chunkSplit: {
        strategy: 'split-by-experience',
        override: {
          chunks: {
            vendor: {
              test: /[\\/]node_modules[\\/]/,
              name: 'vendor',
              priority: 10,
            },
            common: {
              name: 'common',
              minChunks: 2,
              priority: 5,
            },
          },
        },
      },
      // 资源优化
      assetPrefix: process.env.NODE_ENV === 'production' ? '/static' : '',
    },
    tools: {
      // 构建分析
      bundleAnalyzer: process.env.ANALYZE === 'true',
    },
  },
});
```

## 安全最佳实践

### 1. 输入验证

#### 表单验证
```typescript
// utils/validation.ts
export const validationRules = {
  email: (value: string) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(value) || '请输入有效的邮箱地址';
  },
  
  password: (value: string) => {
    if (value.length < 8) return '密码至少需要8个字符';
    if (!/[A-Z]/.test(value)) return '密码必须包含大写字母';
    if (!/[a-z]/.test(value)) return '密码必须包含小写字母';
    if (!/\d/.test(value)) return '密码必须包含数字';
    return true;
  },
  
  required: (value: any) => {
    return value ? true : '此字段为必填项';
  },
};
```

### 2. XSS 防护

#### 内容清理
```typescript
// utils/sanitize.ts
import DOMPurify from 'dompurify';

export function sanitizeHtml(html: string): string {
  return DOMPurify.sanitize(html, {
    ALLOWED_TAGS: ['p', 'br', 'strong', 'em'],
    ALLOWED_ATTR: [],
  });
}

// 使用
function UserContent({ content }: { content: string }) {
  const sanitizedContent = sanitizeHtml(content);
  
  return (
    <div 
      dangerouslySetInnerHTML={{ __html: sanitizedContent }}
    />
  );
}
```

## 监控和调试

### 1. 性能监控

#### 自定义指标
```typescript
// utils/performance.ts
import { actualFMP } from '@ttastra/core/runtime/slardar';

export function trackPageLoad(pageName: string) {
  const startTime = performance.now();
  
  return {
    end: () => {
      const loadTime = performance.now() - startTime;
      actualFMP(`page_load_${pageName}`, loadTime);
    },
  };
}

// 使用
function Dashboard() {
  useEffect(() => {
    const tracker = trackPageLoad('dashboard');
    
    // 页面加载完成后
    const timer = setTimeout(() => {
      tracker.end();
    }, 1000);
    
    return () => clearTimeout(timer);
  }, []);
  
  return <div>Dashboard content</div>;
}
```

### 2. 错误监控

#### 错误边界
```typescript
// components/ErrorBoundary.tsx
interface ErrorBoundaryState {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends React.Component<
  React.PropsWithChildren<{}>,
  ErrorBoundaryState
> {
  constructor(props: React.PropsWithChildren<{}>) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    // 上报错误
    console.error('Error caught by boundary:', error, errorInfo);
    
    // 可以在这里集成错误上报服务
    // errorReportingService.report(error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="error-boundary">
          <h2>Something went wrong</h2>
          <details>
            <summary>Error details</summary>
            <pre>{this.state.error?.stack}</pre>
          </details>
        </div>
      );
    }

    return this.props.children;
  }
}
```

这些最佳实践涵盖了 TTAstra 开发的各个方面，从项目结构到性能优化，从测试到部署，为开发者提供了全面的指导。遵循这些实践可以确保代码质量、性能和可维护性。
