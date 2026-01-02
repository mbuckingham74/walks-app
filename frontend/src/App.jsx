import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Dashboard } from './components/Dashboard';
import { StepsDetail2025 } from './components/StepsDetail2025';
import { StepsDetail2026 } from './components/StepsDetail2026';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/2025" element={<StepsDetail2025 />} />
        <Route path="/2026" element={<StepsDetail2026 />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
