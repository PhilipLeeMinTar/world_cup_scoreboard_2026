# Best Practices

This document provides best practices for using Semi Design components.

## Component Imports

### Recommended Approach

Import components on-demand directly, no additional configuration needed:

```jsx
import { Button, Input, Table, Form, Modal } from "@douyinfe/semi-ui";
```

Semi Design's build output has built-in on-demand loading support, no need to configure babel-plugin-import or other plugins.

### Icon Imports

```jsx
import { IconUser, IconHome, IconSearch } from "@douyinfe/semi-icons";
```

Use the tool get_semi_document with Icon to view all available icons

## Theme Customization

If you need to customize the theme (such as Design Tokens, colors, fonts, etc.), please refer to the official customization documentation:

The documentation includes:

- Theme variable configuration methods
- Dark mode support

Use MCP tools to get the relevant documentation:

```json
{
  "name": "get_semi_document",
  "arguments": {
    "componentName": "customize-theme"
  }
}
```

## React 19 Compatibility

If the project uses React 19, some components may have special usage or considerations.

Use MCP tools to get React 19 related documentation:

```json
{
  "name": "get_semi_document",
  "arguments": {
    "componentName": "react19"
  }
}
```

The documentation includes:

- React 19 new feature usage examples
- Known compatibility issues and solutions
- Performance optimization suggestions

## Extending Components

When requirements cannot be met through props or ref methods, and Semi Design's default functionality doesn't meet your needs, or you need to modify the component's internal logic/styles, it's recommended to extend components through inheritance.

### Step 1: Read Component Source Code

Use MCP tools to get the target component's source code:

```json
{
  "name": "get_component_file_list",
  "arguments": {
    "componentName": "Select"
  }
}
```

After getting the file list, view the specific implementation:

```json
{
  "name": "get_file_code",
  "arguments": {
    "filePath": "@douyinfe/semi-ui/select/index.tsx"
  }
}
```

### Step 2: Create Extended Component

Use class components to inherit from Semi components and override the corresponding methods:

```jsx
import { Select } from "@douyinfe/semi-ui";

class CustomSelect extends Select {
  // Override render method, modify UI
  render() {
    const original = super.render();
    // Add custom content before and after the original Select
    return (
      <div className="custom-select-wrapper">
        <span className="label">{this.props.label}</span>
        {original}
      </div>
    );
  }

  // Override option selection handling, add extra logic
  onSelect(option, optionIndex, e) {
    console.log("Custom selection logic", option);
    // Call original logic
    super.onSelect(option, optionIndex, e);
  }

  // Override lifecycle methods
  componentDidMount() {
    super.componentDidMount();
    console.log("Select mounted");
  }
}
```

### Step 3: Use Extended Component

```jsx
import { CustomSelect } from "./components";

<CustomSelect
  label="Please select"
  dataSource={[
    { value: "apple", label: "Apple" },
    { value: "banana", label: "Banana" },
  ]}
  onChange={(value) => console.log("Selected", value)}
/>;
```

### Overriding Internal Logic Example

Modify Table's sorting behavior:

```jsx
import { Table } from "@douyinfe/semi-ui";

class CustomTable extends Table {
  handleSorterChange = (column, order) => {
    // Add custom sorting logic
    if (this.props.onCustomSort) {
      this.props.onCustomSort(column, order);
    }
    // Call original logic
    super.handleSorterChange(column, order);
  };
}
```

### Considerations

- Only override necessary methods to avoid breaking component encapsulation
- Call `super.xxx()` to preserve original logic

### Use Cases

Inheritance extension is a heavier approach, you should first try to implement through props:

**Prefer using props**:

```jsx
// Most requirements can be met through props
<Button type="primary" loading={loading} onClick={handleClick}>
  Button
</Button>
```

**Only consider extension when props cannot meet requirements**:

- Need to modify the default behavior of component internal methods
- Need to intercept component lifecycle logic
- Need to insert custom logic in the rendering process, or modify component internal UI

For example: need to modify Table's default sorting algorithm, override certain default configurations of Modal, etc.

# Tailwind

If the project uses Tailwind, please use MCP tools to get the relevant documentation:

```json
{
  "name": "get_semi_document",
  "arguments": {
    "componentName": "tailwind"
  }
}
```
