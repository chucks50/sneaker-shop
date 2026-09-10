import { BrowserRouter, Routes, Route, Link } from 'react-router-dom'

function HomePage() {
  return (
    <main>
      <h1>Sneaker Shop</h1>
      <p>Home page placeholder for Sprint 1 setup.</p>
      <nav>
        <Link to="/products">Products</Link>
        <Link to="/cart">Cart</Link>
        <Link to="/login">Login</Link>
      </nav>
    </main>
  )
}

function ProductsPage() {
  return <h2>Products Page</h2>
}

function CartPage() {
  return <h2>Cart Page</h2>
}

function LoginPage() {
  return <h2>Login Page</h2>
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/products" element={<ProductsPage />} />
        <Route path="/cart" element={<CartPage />} />
        <Route path="/login" element={<LoginPage />} />
      </Routes>
    </BrowserRouter>
  )
}
