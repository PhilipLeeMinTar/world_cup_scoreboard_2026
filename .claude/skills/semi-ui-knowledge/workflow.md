# Workflow: Querying Components with MCP Tools

This document describes how to use Semi MCP tools to complete common tasks.

## Semi MCP Tools Overview

| Tool Name                 | Function                             | Use Case                        |
| ------------------------- | ------------------------------------ | ------------------------------- |
| `get_semi_document`       | Get component docs or component list | Find components, understand API |
| `get_component_file_list` | Get component source file list       | Understand component structure  |
| `get_file_code`           | Get file code content                | View component implementation   |
| `get_function_code`       | Get complete function implementation | Deep dive into logic            |

## Basic Query Flow

### 1. Find Components

When you're unsure which component to use, first query the component list:

```json
{
  "name": "get_semi_document"
}
```

Returns all available components list, select the appropriate component.

### 2. Query Component Details

Get the complete documentation for a specified component:

```json
{
  "name": "get_semi_document",
  "arguments": {
    "componentName": "Table"
  }
}
```

### 3. View Component Source Code

Understand the component's internal implementation:

```json
{
  "name": "get_component_file_list",
  "arguments": {
    "componentName": "Table"
  }
}
```

After getting the file list, you can use `get_file_code` to view specific files:

```json
{
  "name": "get_file_code",
  "arguments": {
    "filePath": "@douyinfe/semi-ui/table/Table.tsx"
  }
}
```

### 4. View Function Implementation

Deep dive into a function's logic:

```json
{
  "name": "get_function_code",
  "arguments": {
    "filePath": "@douyinfe/semi-ui/table/Table.tsx",
    "functionName": "render"
  }
}
```

## Complete Task Examples

### Task 1: Create a Table with Filtering

**Goal**: Create a Table component that supports local filtering

**Steps**:

1. **Query Table component documentation**

   ```json
   { "name": "get_semi_document", "arguments": { "componentName": "Table" } }
   ```

2. **Get Table related files**

   ```json
   {
     "name": "get_component_file_list",
     "arguments": { "componentName": "Table" }
   }
   ```

3. **View filtering related source code**

   - View filtering logic in `foundation.ts`
   - View implementation of `filter.tsx`
   - View `columns.tsx` to understand column configuration

4. **View onFilter example**

   ```json
   {
     "name": "get_function_code",
     "arguments": {
       "filePath": "@douyinfe/semi-ui/table/table.tsx",
       "functionName": "handleFilter"
     }
   }
   ```

5. **Generate code**
   Based on query results, generate compliant Table filtering code

### Task 2: Customize Table Columns

**Goal**: Create a Table that supports custom column rendering

**Steps**:

1. **Query Table documentation** to understand column configuration options
2. **Query Column component** (if there's separate documentation)
3. **View render function implementation** to understand how to customize cells
4. **Generate code** to create custom column configuration

### Task 3: Implement Form Validation

**Goal**: Create a form with complex validation logic

**Steps**:

1. **Query Form component documentation**

   ```json
   { "name": "get_semi_document", "arguments": { "componentName": "Form" } }
   ```

2. **Get Form related files**

   ```json
   {
     "name": "get_component_file_list",
     "arguments": { "componentName": "Form" }
   }
   ```

3. **View validation related code**

   - View `rules.ts` or validation logic files
   - View `label.tsx` to understand label configuration

4. **Generate form code**, including:
   - Required field validation
   - Format validation (email, phone number)
   - Custom validation functions

### Task 4: Create Cascading Selector

**Goal**: Implement province-city-district three-level cascading selection

**Steps**:

1. **Query Cascader component documentation**

   ```json
   { "name": "get_semi_document", "arguments": { "componentName": "Cascader" } }
   ```

2. **View data structure examples**

   - View the data format in the component
   - Understand loadData or onChange usage

3. **Generate cascading selector code**

### Task 5: Implement Drag-and-Drop Sorting

**Goal**: Create a Table that supports row drag-and-drop sorting

**Steps**:

1. **Query Table component** to see if drag-and-drop is built-in
2. **Query Sortable component** (if available)
3. **View drag-and-drop related source code**
4. **Generate Table code with drag-and-drop functionality**

## Common Query Tips

### 1. Version-Specific Query

```json
{
  "name": "get_semi_document",
  "arguments": {
    "componentName": "Button",
    "version": "2.89.2"
  }
}
```

### 2. Get Component File List

Get all file paths for a component:

```json
{
  "name": "get_component_file_list",
  "arguments": {
    "componentName": "Table"
  }
}
```

### 3. View Complete Code (No Truncation)

```json
{
  "name": "get_file_code",
  "arguments": {
    "filePath": "@douyinfe/semi-ui/button/Button.tsx",
    "fullCode": true
  }
}
```

## Error Troubleshooting Flow

When encountering issues, follow these steps to troubleshoot:

1. **Confirm component name is correct** (case-insensitive)
2. **Confirm file path is correct** (refer to the path returned by `get_path`)
3. **Confirm function name exists** (can search in source code)
4. **Check error message** (usually indicates where the problem is)

### Common Errors and Solutions

**Error 1: Component Not Found**

- Confirm component name spelling is correct
- Use `get_semi_document` to get the complete list

**Error 2: File Path Error**

- Use `get_component_file_list` to get the correct path
- Pay attention to case sensitivity and path separators

**Error 3: Function Does Not Exist**

- Confirm function name is accurate
- Use `get_file_code` to view file content and confirm function name
