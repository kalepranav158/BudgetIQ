import { useState } from "react";
import Button from "../components/ui/Button";
import KeywordMappingTab from "../features/mappings/KeywordMappingTab";
import RegexMappingTab from "../features/mappings/RegexMappingTab";

function MappingsPage() {
  const [activeTab, setActiveTab] = useState("keyword");

  return (
    <section className="page">
      <h1 className="page-title">Mappings</h1>
      <p className="page-subtitle">Manage keyword and regex category mappings.</p>
      <div className="tab-row" role="tablist" aria-label="Mappings tabs">
        <Button
          variant={activeTab === "keyword" ? "primary" : "secondary"}
          onClick={() => setActiveTab("keyword")}
          role="tab"
          aria-selected={activeTab === "keyword"}
        >
          Keywords
        </Button>
        <Button
          variant={activeTab === "regex" ? "primary" : "secondary"}
          onClick={() => setActiveTab("regex")}
          role="tab"
          aria-selected={activeTab === "regex"}
        >
          Regex Rules
        </Button>
      </div>
      <div className="tab-panel">{activeTab === "keyword" ? <KeywordMappingTab /> : <RegexMappingTab />}</div>
    </section>
  );
}

export default MappingsPage;
