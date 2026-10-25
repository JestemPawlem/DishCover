import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { MainLayout } from './components/MainLayout';
import { Dashboard } from './pages/Dashboard';
import { Favorites } from './pages/Favorites';
import { SearchResults } from './pages/SearchResults';
import { RecipeDetails } from './pages/RecipeDetails';
import { Login } from './pages/Login';
import { Register } from './pages/Register';

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<MainLayout />}>
          <Route path='/' element={<Dashboard />} />
          <Route path='/favorites' element={<Favorites />} />
          <Route path='/search' element={<SearchResults />} />
          <Route path='/recipes/:id' element={<RecipeDetails />} />
        </Route>
        <Route path='/login' element={<Login />} />
        <Route path='/register' element={<Register />} />
        <Route path='*' element={<Navigate to='/' replace />} />
      </Routes>
    </BrowserRouter>
  );
}