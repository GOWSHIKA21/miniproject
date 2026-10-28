import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

export default function KnowledgeGraph() {
  const navigate = useNavigate();

  useEffect(() => {
    navigate('/explorer', { replace: true });
  }, [navigate]);

  return null;
}
