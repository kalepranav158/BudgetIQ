import { useState } from "react";
import Button from "../../components/ui/Button";
import Input from "../../components/ui/Input";
import Select from "../../components/ui/Select";
import { CATEGORIES } from "../../constants/categories";

const CUSTOM_CATEGORY_VALUE = "__custom__";

function normalizeCategory(value) {
  return value.trim().toLowerCase().replace(/\s+/g, "_");
}

function getCategoryOptions(categories) {
  const source = ["other", ...CATEGORIES, ...(categories || [])];
  const deduped = Array.from(new Set(source.map((item) => normalizeCategory(String(item || ""))).filter(Boolean)));
  return deduped;
}

function MappingCreateForm({ type, onSubmit, pending, categories = [] }) {
  const [values, setValues] = useState({
    keyword: "",
    name: "",
    pattern: "",
    category: "",
    customCategory: "",
    priority: "100"
  });
  const [errors, setErrors] = useState({});

  const isKeyword = type === "keyword";

  const updateValue = (key, value) => {
    setValues((current) => ({ ...current, [key]: value }));
  };

  const categoryOptions = getCategoryOptions(categories);
  const resolvedCategory =
    values.category === CUSTOM_CATEGORY_VALUE ? normalizeCategory(values.customCategory) : normalizeCategory(values.category);

  const validate = () => {
    const nextErrors = {};

    if (isKeyword) {
      if (!values.keyword.trim()) {
        nextErrors.keyword = "Keyword is required.";
      }
    } else {
      if (!values.name.trim()) {
        nextErrors.name = "Name is required.";
      }
      if (!values.pattern.trim()) {
        nextErrors.pattern = "Pattern is required.";
      }
      if (values.priority && Number(values.priority) < 1) {
        nextErrors.priority = "Priority must be a positive number.";
      }
    }

    if (!values.category) {
      nextErrors.category = "Please select a category.";
    } else if (values.category === CUSTOM_CATEGORY_VALUE && !normalizeCategory(values.customCategory)) {
      nextErrors.customCategory = "Please enter a category name.";
    }

    setErrors(nextErrors);
    return Object.keys(nextErrors).length === 0;
  };

  const reset = () => {
    setValues({
      keyword: "",
      name: "",
      pattern: "",
      category: "",
      customCategory: "",
      priority: "100"
    });
    setErrors({});
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!validate()) {
      return;
    }

    const payload = isKeyword
        ? { keyword: values.keyword.trim(), category: resolvedCategory }
      : {
          name: values.name.trim(),
          pattern: values.pattern.trim(),
          category: resolvedCategory,
          priority: values.priority || "100"
        };

    const result = await onSubmit(payload);
    if (result?.ok) {
      reset();
    }
  };

  return (
    <form className="stack" onSubmit={handleSubmit}>
      {isKeyword ? (
        <Input
          id="mapping-keyword"
          label="Keyword"
          value={values.keyword}
          onChange={(event) => updateValue("keyword", event.target.value)}
          error={errors.keyword}
        />
      ) : (
        <>
          <Input
            id="mapping-name"
            label="Name"
            value={values.name}
            onChange={(event) => updateValue("name", event.target.value)}
            error={errors.name}
          />
          <Input
            id="mapping-pattern"
            label="Pattern"
            placeholder="Supports regex, e.g. SWIGGY|ZOMATO"
            value={values.pattern}
            onChange={(event) => updateValue("pattern", event.target.value)}
            error={errors.pattern}
          />
          <Input
            id="mapping-priority"
            label="Priority"
            type="number"
            min="1"
            value={values.priority}
            onChange={(event) => updateValue("priority", event.target.value)}
            error={errors.priority}
          />
        </>
      )}

      <Select
        id="mapping-category"
        label="Category"
        value={values.category}
        onChange={(event) => {
          const nextValue = event.target.value;
          updateValue("category", nextValue);
          if (nextValue !== CUSTOM_CATEGORY_VALUE) {
            updateValue("customCategory", "");
          }
        }}
        error={errors.category}
      >
        <option value="">Select a category</option>
        {categoryOptions.map((item) => (
          <option key={item} value={item}>
            {item}
          </option>
        ))}
        <option value={CUSTOM_CATEGORY_VALUE}>+ Create new category</option>
      </Select>

      {values.category === CUSTOM_CATEGORY_VALUE ? (
        <Input
          id="mapping-custom-category"
          label="New Category"
          placeholder="e.g. breakfast"
          value={values.customCategory}
          onChange={(event) => updateValue("customCategory", event.target.value)}
          error={errors.customCategory}
        />
      ) : null}

      <Button type="submit" loading={pending}>
        {isKeyword ? "Add Mapping" : "Add Rule"}
      </Button>
    </form>
  );
}

export default MappingCreateForm;
