import { useEffect, useState } from "react";
import SkillInput from "./components/SkillInput";
import JobResults from "./components/JobResults";
import SkillGap from "./components/SkillGap";
import TrendChart from "./components/TrendChart";

function App() {
  const [trending, setTrending] = useState([]);
  const [results, setResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchTrending = async () => {
      try {
        setError("");
        const response = await fetch("http://localhost:5000/api/trending");

        if (!response.ok) {
          throw new Error("Failed to fetch trending skills");
        }

        const data = await response.json();
        setTrending(Array.isArray(data) ? data : []);
      } catch (err) {
        setError(err.message || "Something went wrong");
      }
    };

    fetchTrending();
  }, []);

  const handleAnalyze = async (skills) => {
    try {
      setError("");
      setIsLoading(true);

      const response = await fetch("http://localhost:5000/api/analyze", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ skills }),
      });

      if (!response.ok) {
        throw new Error("Failed to analyze skills");
      }

      const data = await response.json();
      setResults(Array.isArray(data) ? data : []);
    } catch (err) {
      setError(err.message || "Something went wrong");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div>
      {error && <p>{error}</p>}
      <SkillInput onAnalyze={handleAnalyze} isLoading={isLoading} />
      <TrendChart trending={trending} />
      <JobResults results={results} />
      <SkillGap results={results} />
    </div>
  );
}

export default App;
