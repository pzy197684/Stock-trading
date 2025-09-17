// 
// 整个 JavaScript 应用的入口文件。
// 它的工作是找到页面上的根元素（通常在 index.html 里），
// 然后用 React 把 App 组件“渲染”或“挂载”到那个元素上，
// 从而启动整个 React 应用。
// 
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
