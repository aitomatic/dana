# Textual Framework Guide for AI Coders

## Overview
Textual is a Python framework for building sophisticated terminal user interfaces (TUIs) with rich interactivity, styling, and modern UI patterns. It enables creating applications that run in the terminal but feel like modern GUI applications.

## Core Concepts

### 1. Application Structure
Every Textual app inherits from `App` class:
```python
from textual.app import App
from textual.widgets import Header, Footer, Button

class MyApp(App):
    """Main application class"""
    
    # Define screens
    SCREENS = {
        "main": MainScreen,
        "settings": SettingsScreen
    }
    
    # Define key bindings
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("d", "toggle_dark", "Toggle dark mode"),
    ]
    
    def compose(self):
        """Build the app layout"""
        yield Header()
        yield Container(id="main-content")
        yield Footer()
    
    def on_mount(self):
        """Called when app starts"""
        self.title = "My Textual App"
```

### 2. Widget System

#### Base Widget Class
All UI components inherit from `Widget`:
```python
from textual.widget import Widget
from textual.reactive import reactive

class Counter(Widget):
    """Custom counter widget"""
    
    count = reactive(0)  # Reactive property
    
    def compose(self):
        """Define widget structure"""
        yield Button("Increment", id="inc")
        yield Label(str(self.count))
    
    def on_button_pressed(self, event):
        """Handle button press"""
        self.count += 1
    
    def watch_count(self, old_value, new_value):
        """React to count changes"""
        self.query_one(Label).update(str(new_value))
```

#### Common Built-in Widgets
- **Input Controls**: `Button`, `Input`, `TextArea`, `Checkbox`, `Switch`, `RadioButton`
- **Display**: `Label`, `Static`, `RichLog`, `ProgressBar`
- **Containers**: `Container`, `Horizontal`, `Vertical`, `Grid`, `ScrollableContainer`
- **Lists**: `ListView`, `OptionList`, `DataTable`, `Tree`, `DirectoryTree`
- **Navigation**: `Tabs`, `TabbedContent`, `Header`, `Footer`

### 3. Reactive System

Textual's reactive properties automatically update the UI when values change:

```python
class ReactiveExample(Widget):
    # Different reactive configurations
    status = reactive("idle")                    # Basic reactive
    progress = reactive(0, layout=True)          # Triggers layout
    message = reactive("", repaint=False)        # No auto-repaint
    enabled = reactive(True, init=False)         # No initial watcher call
    
    def watch_status(self, old, new):
        """Automatically called when status changes"""
        self.add_class(f"status-{new}")
        self.remove_class(f"status-{old}")
```

### 4. Event System

Events bubble up through the widget hierarchy:

```python
class EventExample(Widget):
    def on_key(self, event):
        """Handle any key press"""
        if event.key == "escape":
            self.app.exit()
    
    def on_click(self, event):
        """Handle mouse clicks"""
        self.log(f"Clicked at {event.x}, {event.y}")
    
    def on_focus(self):
        """Widget gained focus"""
        self.add_class("focused")
    
    def on_blur(self):
        """Widget lost focus"""
        self.remove_class("focused")
```

### 5. CSS Styling System

Textual uses a sophisticated CSS-like styling system with some unique features:

#### CSS Selectors
```css
/* Type selector - matches widget class */
Button { background: $primary; }

/* ID selector - unique identifier */
#submit-btn { border: thick $success; }

/* Class selector - can be added/removed dynamically */
.danger { background: red; }

/* Pseudo-classes */
Button:hover { background: $primary-lighten-1; }
Button:focus { border: thick $accent; }
Button:disabled { opacity: 0.5; }

/* Combinators */
Container Button { margin: 1; }  /* Descendant */
Container > Button { padding: 2; }  /* Direct child */

/* Nested CSS (v0.47.0+) */
#questions {
    background: $surface;
    .button {
        margin: 1;
        &.affirmative {
            border: heavy $success;
        }
        &:hover {
            background: $primary 20%;
        }
    }
}
```

#### CSS Properties Reference

##### Layout & Sizing
- `width`, `height`: Set dimensions (auto, %, fr, vh/vw, pixels)
- `min-width`, `min-height`, `max-width`, `max-height`: Size constraints
- `display`: none | block
- `visibility`: visible | hidden
- `dock`: top | right | bottom | left
- `layer`: Set z-order for overlapping widgets
- `offset`: x y coordinates for positioning
- `content-align`: Align content within widget
- `align`: Align widget within parent (horizontal vertical)
- `text-align`: left | center | right | justify

##### Spacing & Box Model
- `padding`: Space inside widget border (1-4 values)
- `margin`: Space outside widget (1-4 values)
- `border`: Style width color (e.g., `solid 1 $primary`)
  - Styles: ascii, blank, double, heavy, hidden, none, round, solid, thick
- `outline`: Like border but doesn't affect layout
- `box-sizing`: border-box | content-box
- `overflow`: visible | hidden | scroll | auto
- `overflow-x`, `overflow-y`: Control per axis

##### Colors & Effects
- `background`: Color with optional transparency
- `color`: Text/foreground color
- `opacity`: 0.0 to 1.0
- `text-opacity`: Specifically for text
- `tint`: Apply color overlay to entire widget

##### Text Styling
- `text-style`: bold | italic | reverse | underline | strike | overline
- `link-color`: Color for hyperlinks
- `link-background`: Background for hyperlinks
- `link-style`: Style for hyperlinks

##### Scrollbar Styling
- `scrollbar-background`: Scrollbar track color
- `scrollbar-color`: Scrollbar thumb color
- `scrollbar-corner-color`: Corner where scrollbars meet
- `scrollbar-gutter`: stable | auto
- `scrollbar-size`: Width/height of scrollbars

#### Color Formats
```css
/* Named colors */
background: crimson;

/* Hex colors */
background: #ff6347;

/* RGB */
background: rgb(255, 99, 71);

/* HSL */
background: hsl(9, 100%, 64%);

/* With transparency */
background: rgb(255, 99, 71, 0.5);
background: $primary 50%;  /* Theme color with transparency */
```

#### CSS Variables & Themes
```css
/* Using theme variables */
Button {
    background: $primary;
    color: $text;
    border: solid $surface-edge;
}

/* Dark/light mode specific */
Button:dark {
    background: $panel;
}

Button:light {
    background: $surface;
}
```

#### Units System
- **Pixels**: `10` (integer values)
- **Percentage**: `50%` (of parent dimension)
- **Viewport**: `50vw`, `25vh` (of terminal size)
- **Fractional**: `1fr`, `2fr` (flexible space distribution)
- **Auto**: `auto` (content-based sizing)
- **Character cells**: Default unit for terminal

#### Dynamic Styling in Python
```python
class StyledWidget(Widget):
    DEFAULT_CSS = """
    StyledWidget {
        background: $surface;
        border: solid $primary;
        padding: 1 2;
        margin: 1;
    }
    
    StyledWidget:hover {
        background: $primary 20%;
    }
    
    StyledWidget.active {
        border: thick $success;
    }
    """
    
    def on_mount(self):
        # Dynamic styling via styles object
        self.styles.width = "50%"
        self.styles.height = 10
        self.styles.background = "darkblue"
        self.styles.border = ("heavy", "yellow")
        
        # Add/remove CSS classes
        self.add_class("active")
        self.remove_class("inactive")
        self.toggle_class("highlighted")
```

#### CSS Loading Methods
```python
# Method 1: DEFAULT_CSS class variable
class MyWidget(Widget):
    DEFAULT_CSS = """
    MyWidget { background: blue; }
    """

# Method 2: External CSS file
class MyApp(App):
    CSS_PATH = "styles.tcss"

# Method 3: Inline CSS
class MyApp(App):
    CSS = """
    Screen { background: $surface; }
    """

# Method 4: Load CSS dynamically
app.stylesheet.add_source(css_content, path="dynamic.tcss")
```

#### CSS Specificity Rules
Priority order (highest to lowest):
1. Inline styles (via `styles` object)
2. ID selectors
3. Class selectors
4. Type selectors
5. Universal selector

Within same specificity level:
- Later rules override earlier ones
- More specific selectors win

## Screens and Navigation

### Screen Fundamentals
Screens are full-terminal containers that manage widget layouts:
- Only one screen is visible at a time
- Managed via a screen stack
- Support modal overlays and transitions

### Screen Stack Operations
```python
# Push new screen onto stack
self.app.push_screen("settings")

# Pop current screen
self.app.pop_screen()

# Replace current screen
self.app.switch_screen("main")

# Push and wait for result
result = await self.app.push_screen_wait(ConfirmScreen())
```

### Modal Screens
```python
from textual.screen import ModalScreen

class Dialog(ModalScreen[bool]):
    """Modal dialog that returns a boolean"""
    
    BINDINGS = [("escape", "dismiss(False)", "Cancel")]
    
    def compose(self):
        yield Grid(
            Label("Are you sure?"),
            Button("Yes", id="yes"),
            Button("No", id="no"),
        )
    
    def on_button_pressed(self, event):
        self.dismiss(event.button.id == "yes")
```

### Application Modes
```python
class MyApp(App):
    MODES = {
        "main": "main",
        "edit": "edit",
        "help": "help",
    }
    
    def on_mount(self):
        self.switch_mode("main")
```

## Workers and Concurrency

### Worker Basics
Workers handle background tasks without blocking the UI:

```python
from textual import work

class DataWidget(Widget):
    @work(exclusive=True)
    async def load_data(self, url: str):
        """Load data in background"""
        response = await httpx.get(url)
        self.update_display(response.json())
    
    @work(thread=True)
    def process_file(self, path: str):
        """Process file in thread worker"""
        with open(path) as f:
            data = f.read()
        self.call_from_thread(self.update_display, data)
```

### Worker Features
- **Exclusive workers**: Cancel previous instance when called again
- **Thread workers**: For synchronous/blocking code
- **Worker state**: Track PENDING, RUNNING, SUCCESS, ERROR, CANCELLED
- **Cancellation**: Support graceful cancellation

### Worker State Handling
```python
def on_worker_state_changed(self, event):
    """React to worker state changes"""
    if event.state == WorkerState.SUCCESS:
        self.notify("Task completed!")
    elif event.state == WorkerState.ERROR:
        self.notify(f"Error: {event.error}", severity="error")
```

## Testing Textual Apps

### Test Setup
```python
import pytest
from textual.pilot import Pilot

@pytest.mark.asyncio
async def test_app():
    app = MyApp()
    async with app.run_test() as pilot:
        # Simulate user interactions
        await pilot.press("tab")
        await pilot.click("#submit")
        await pilot.type("Hello")
        
        # Assert app state
        assert app.query_one("#output").renderable == "Hello"
```

### Pilot Actions
- `press(key)`: Simulate key press
- `click(selector)`: Click on widget
- `type(text)`: Type text input
- `hover(selector)`: Hover over widget
- `scroll(x, y)`: Scroll content
- `pause()`: Wait for message processing
- `resize(width, height)`: Resize terminal

### Snapshot Testing
```python
# Install: pip install pytest-textual-snapshot

@pytest.mark.asyncio
async def test_snapshot(snap_compare):
    assert snap_compare("path/to/app.py", press=["tab", "enter"])
```

## Content and Rendering

### Rich Markup
```python
from textual.widgets import Static

class RichContent(Static):
    def compose(self):
        yield Static(
            "[bold red]Bold red text[/bold red]\n"
            "[link=https://example.com]Clickable link[/link]\n"
            "[reverse]Reversed text[/reverse]"
        )
```

### Content Formatting
- **Styles**: `[bold]`, `[italic]`, `[underline]`, `[strike]`
- **Colors**: `[red]`, `[#ff0000]`, `[rgb(255,0,0)]`
- **Links**: `[link=url]text[/link]`
- **Actions**: `[@click=action]clickable[/@click]`

### Custom Rendering
```python
from rich.console import RenderableType

class CustomWidget(Widget):
    def render(self) -> RenderableType:
        """Return any Rich renderable"""
        return Panel("Custom content", border_style="blue")
    
    def render_line(self, y: int) -> Strip:
        """Advanced line-by-line rendering"""
        # Return Strip with Segments for performance
        pass
```

## Advanced Reactivity

### Reactive Features
```python
class AdvancedReactive(Widget):
    # Validation
    count = reactive(0)
    
    def validate_count(self, value: int) -> int:
        """Validate and modify reactive values"""
        return max(0, min(100, value))
    
    # Computed properties
    def compute_percentage(self) -> str:
        """Computed from other reactive properties"""
        return f"{self.count}%"
    
    # Dynamic defaults
    items = reactive(lambda: [])
    
    # Set without triggering watchers
    def on_mount(self):
        self.set_reactive(AdvancedReactive.count, 50)
```

### Data Binding
```python
class DataBinding(App):
    value = reactive("")
    
    def compose(self):
        yield Input(value=self.value)
        yield Label()
    
    def watch_value(self, value: str):
        self.query_one(Label).update(f"You typed: {value}")
```

## Actions System

### Defining Actions
```python
class ActionApp(App):
    def action_set_theme(self, theme: str):
        """Action callable from links and bindings"""
        self.theme = theme
    
    def check_action(self, action: str, parameters: tuple) -> bool:
        """Control action availability"""
        if action == "set_theme":
            return parameters[0] in self.available_themes
        return True
```

### Using Actions
```python
# In key bindings
BINDINGS = [
    ("d", "set_theme('dark')", "Dark theme"),
    ("l", "set_theme('light')", "Light theme"),
]

# In markup
static = Static("[@click=set_theme('dark')]Switch to dark[@click]")

# Programmatically
await self.run_action("set_theme('dark')")
```

### Action Namespaces
- `app.action()`: Target app
- `screen.action()`: Target current screen
- `focused.action()`: Target focused widget

## Input Handling

### Keyboard Input
```python
class InputHandler(Widget):
    can_focus = True  # Make focusable
    
    def on_key(self, event):
        if event.key == "ctrl+c":
            self.copy_to_clipboard()
        elif event.character and event.is_printable:
            self.add_character(event.character)
```

### Mouse Input
```python
class MouseHandler(Widget):
    def on_mouse_move(self, event):
        self.hover_position = (event.x, event.y)
    
    def on_click(self, event):
        if event.button == 1:  # Left click
            self.select_at(event.x, event.y)
    
    def on_mouse_scroll_down(self, event):
        self.scroll_down()
```

### Focus Management
```python
# Set focus
widget.focus()

# Check focus
if widget.has_focus:
    # Widget is focused

# Focus events
def on_focus(self):
    self.add_class("focused")

def on_blur(self):
    self.remove_class("focused")
```

## Advanced Events

### Event Handling Patterns
```python
from textual import on

class EventWidget(Widget):
    # Method naming convention
    def on_button_pressed(self, event):
        """Handle any button press"""
        pass
    
    # Decorator with selector
    @on(Button.Pressed, "#submit")
    def handle_submit(self, event):
        """Handle specific button"""
        pass
    
    # Prevent default behavior
    def on_key(self, event):
        if event.key == "enter":
            event.prevent_default()
            self.custom_enter_handler()
    
    # Stop propagation
    def on_click(self, event):
        event.stop()  # Don't bubble up
```

### Custom Messages
```python
from textual.message import Message

class DataUpdate(Message):
    """Custom message for data updates"""
    def __init__(self, data: dict):
        super().__init__()
        self.data = data

class DataWidget(Widget):
    def update_data(self, data: dict):
        # Post message to parent
        self.post_message(DataUpdate(data))

class ParentWidget(Widget):
    def on_data_update(self, message: DataUpdate):
        # Handle data update from child
        self.process_data(message.data)
```

## Layout System

### Layout Types
```css
/* Vertical layout */
Container {
    layout: vertical;
}

/* Horizontal layout */
Container {
    layout: horizontal;
}

/* Grid layout */
Container {
    layout: grid;
    grid-size: 3 2;  /* 3 columns, 2 rows */
    grid-columns: 1fr 2fr 1fr;
    grid-rows: auto 1fr;
}
```

### Container Widgets
```python
from textual.containers import Container, Horizontal, Vertical, Grid

def compose(self):
    with Vertical():
        yield Header()
        with Horizontal():
            yield Sidebar()
            yield Content()
        yield Footer()
```

### Advanced Layout
```css
/* Docking */
Widget {
    dock: top;  /* top, right, bottom, left */
}

/* Layers */
Widget {
    layer: modal;  /* z-order control */
}

/* Alignment */
Widget {
    align: center middle;
    content-align: center middle;
}
```

## DOM Queries

### Query Methods
```python
# Get single widget
button = self.query_one("#submit", Button)

# Get multiple widgets
buttons = self.query("Button")

# Filter by type
inputs = self.query("Input").results(Input)

# Complex selectors
disabled = self.query(".form Button:disabled")
```

### Query Operations
```python
# Batch operations
self.query("Button").add_class("highlight")
self.query(".old").remove()

# Filtering
active = self.query("Widget").filter(".active")
visible = self.query("Widget").exclude(".hidden")

# First/last
first_btn = self.query("Button").first()
last_input = self.query("Input").last()
```

## Developer Tools

### Development Mode
```bash
# Run with live CSS reloading
textual run --dev myapp.py

# Open devtools console
textual console

# Serve app in browser
textual serve myapp.py
```

### Debugging
```python
from textual import log

class DebugWidget(Widget):
    def on_mount(self):
        # Log to devtools console
        log("Widget mounted")
        log(self.size, self.region)
        
        # Pretty print objects
        log.debug(complex_object)
        
        # Log with labels
        log(width=self.size.width, height=self.size.height)
```

### Console Options
```bash
# Verbose output
textual console -v

# Exclude message types
textual console -x EVENT -x SYSTEM

# Clear on startup
textual console --clear
```

## Common Patterns

### 1. Loading Indicators
```python
class LoadingWidget(Widget):
    loading = reactive(False)
    
    def compose(self):
        yield LoadingIndicator()
        yield Container(id="content")
    
    @work(exclusive=True)
    async def load_data(self):
        self.loading = True
        try:
            data = await fetch_data()
            self.update_content(data)
        finally:
            self.loading = False
    
    def watch_loading(self, loading: bool):
        self.query_one(LoadingIndicator).display = loading
```

### 2. Form Validation
```python
class ValidatedForm(Widget):
    email = reactive("")
    
    def validate_email(self, email: str) -> str:
        if "@" not in email:
            self.query_one("#error").update("Invalid email")
            raise ValueError("Invalid email")
        return email.lower()
    
    def on_input_changed(self, event):
        try:
            self.email = event.value
            self.query_one("#submit").disabled = False
        except ValueError:
            self.query_one("#submit").disabled = True
```

### 3. Command Palette
```python
from textual.command import Command, CommandPalette

class CommandApp(App):
    def compose(self):
        yield CommandPalette()
    
    def get_command_palette_commands(self):
        yield Command("Toggle dark mode", self.action_toggle_dark)
        yield Command("Open settings", self.push_screen, "settings")
        yield Command("Export data", self.export_data)
```

### 4. Notifications
```python
class NotificationApp(App):
    def notify_success(self, message: str):
        self.notify(message, severity="information")
    
    def notify_error(self, error: str):
        self.notify(error, severity="error", timeout=10)
    
    def notify_warning(self, warning: str):
        self.notify(warning, severity="warning")
```

### 5. Theme Switching
```python
class ThemedApp(App):
    theme = reactive("dark")
    
    CSS = """
    Screen:light {
        background: white;
        color: black;
    }
    
    Screen:dark {
        background: $surface;
        color: $text;
    }
    """
    
    def action_toggle_theme(self):
        self.theme = "light" if self.theme == "dark" else "dark"
        self.refresh_css()
```

### 6. Tooltips
```python
class TooltipWidget(Widget):
    def compose(self):
        yield Button(
            "Help",
            tooltip="Click for more information"
        )
    
    # Dynamic tooltips
    def get_tooltip(self) -> str:
        return f"Status: {self.status}"
```

### 7. Tab Navigation
```python
from textual.widgets import Tabs, TabbedContent, TabPane

class TabbedApp(App):
    def compose(self):
        with TabbedContent():
            with TabPane("General", id="general-tab"):
                yield GeneralSettings()
            with TabPane("Advanced", id="advanced-tab"):
                yield AdvancedSettings()
            with TabPane("About", id="about-tab"):
                yield AboutInfo()
```

### 8. Dynamic Widget Creation
```python
class DynamicList(Widget):
    items = reactive([])
    
    def watch_items(self, items):
        container = self.query_one("#item-container")
        container.remove_children()
        
        for item in items:
            container.mount(
                ListItem(
                    Label(item.name),
                    Button("Delete", id=f"delete-{item.id}")
                )
            )
```

## Best Practices for AI Coders

### 1. Widget Composition
- Break UI into small, reusable widgets
- Use `compose()` method to define widget hierarchy
- Leverage containers for layout management

### 2. State Management
- Use reactive properties for UI state
- Implement watchers for state changes
- Keep state centralized in the App class for complex apps

### 3. Event Handling
- Use specific event handlers (on_button_pressed) over generic ones
- Stop event propagation when handled: `event.stop()`
- Leverage message passing for decoupled communication

### 4. Performance
- Use `work` decorator for async operations
- Implement virtual scrolling for large lists
- Minimize reactive property updates

### 5. Testing
```python
async def test_app():
    app = MyApp()
    async with app.run_test() as pilot:
        await pilot.press("tab")  # Navigate
        await pilot.click("#button")  # Click button
        await pilot.type("Hello")  # Type text
        assert app.query_one("#label").renderable == "Hello"
```

## Quick Reference

### Essential Imports
```python
from textual.app import App, ComposeResult
from textual.widgets import Button, Input, Label, Static
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive, var
from textual.screen import Screen
from textual import events, work
```

### App Lifecycle Methods
- `compose()` - Define app structure
- `on_mount()` - App started
- `on_load()` - Before first paint
- `on_ready()` - App fully loaded
- `action_*()` - Handle key bindings

### Widget Lifecycle Methods
- `compose()` - Define widget structure
- `on_mount()` - Widget added to DOM
- `render()` - Return renderable content
- `on_blur()` / `on_focus()` - Focus changes
- `watch_*()` - React to reactive changes

### CSS Quick Reference

#### Most Used Properties
- **Sizing**: `width`, `height` (auto, 50%, 1fr, 10)
- **Spacing**: `padding: 1 2`, `margin: 1`
- **Colors**: `background: $primary`, `color: white`
- **Borders**: `border: solid $accent`, `outline: heavy blue`
- **Layout**: `dock: top`, `align: center middle`
- **Display**: `display: none`, `visibility: hidden`

#### Common Pseudo-Classes
- `:hover` - Mouse over widget
- `:focus` - Widget has focus
- `:disabled` - Widget is disabled
- `:dark` / `:light` - Theme mode
- `:focus-within` - Widget or child has focus
- `:first-child` / `:last-child` - Position selectors

#### Border Styles
`ascii`, `blank`, `double`, `heavy`, `hidden`, `none`, `round`, `solid`, `thick`

#### Theme Variables
`$primary`, `$secondary`, `$surface`, `$panel`, `$error`, `$warning`, `$success`, `$accent`, `$text`, `$text-muted`, `$text-disabled`

## Example: Complete Mini App

```python
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.reactive import reactive
from textual.widgets import Button, Header, Input, Label, ListView, ListItem, Footer

class TodoApp(App):
    """A simple todo list application"""
    
    CSS = """
    Container {
        padding: 1;
    }
    
    #input-area {
        dock: top;
        height: 3;
    }
    
    ListView {
        border: solid $primary;
    }
    """
    
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("a", "add_todo", "Add Todo"),
    ]
    
    todos = reactive([])
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Horizontal(
                Input(placeholder="Enter todo...", id="todo-input"),
                Button("Add", variant="primary", id="add-btn"),
                id="input-area"
            ),
            ListView(id="todo-list"),
        )
        yield Footer()
    
    def on_button_pressed(self, event):
        if event.button.id == "add-btn":
            self.add_todo()
    
    def action_add_todo(self):
        input_widget = self.query_one("#todo-input", Input)
        if todo_text := input_widget.value:
            self.todos = self.todos + [todo_text]
            input_widget.value = ""
    
    def watch_todos(self, todos):
        list_view = self.query_one("#todo-list", ListView)
        list_view.clear()
        for todo in todos:
            list_view.append(ListItem(Label(todo)))

if __name__ == "__main__":
    app = TodoApp()
    app.run()
```

## Resources
- Documentation: https://textual.textualize.io/
- API Reference: https://textual.textualize.io/api/
- Widget Gallery: https://textual.textualize.io/widgets/
- GitHub: https://github.com/Textualize/textual