import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ErrorBoundary } from './components/ErrorBoundary';
import { Dashboard } from './components/Dashboard';
import { StepsDetail } from './components/StepsDetail';
import { StatsPage } from './components/StatsPage';

function App() {
  return (
    <BrowserRouter>
      <ErrorBoundary>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/stats" element={<StatsPage />} />
          <Route path="/:year" element={<StepsDetail />} />
        </Routes>
      </ErrorBoundary>
    </BrowserRouter>
  );
}

export default App;
