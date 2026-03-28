import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Dashboard } from './components/Dashboard';
import { StepsDetail } from './components/StepsDetail';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/:year" element={<StepsDetail />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
