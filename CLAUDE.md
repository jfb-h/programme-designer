# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Django web application for designing and managing university study programmes. It tracks courses, modules, programmes, and revisions with comprehensive data modeling for academic programme management.

## Key Development Commands

- **Run development server**: `uv run python manage.py runserver`
- **Create and apply migrations**: `uv run python manage.py makemigrations` then `uv run python manage.py migrate`
- **Run tests**: `uv run python manage.py test`
- **Create superuser**: `uv run python manage.py createsuperuser`
- **Collect static files**: `uv run python manage.py collectstatic`
- **Create sample data**: `uv run python manage.py create_sample_data`

## Architecture Overview

The application consists of two main Django apps:

### studyprogrammes (V1 - Legacy)
- Simple hierarchical structure: Programme → Semester → Course
- Basic CRUD operations with drag-and-drop course management
- User authentication and programme ownership
- SQLite database with basic relationships

### studyprogrammes_v2 (V2 - Current)
- More complex domain model: Course → Module → Programme → Revision
- Advanced features: course sharing, LPO relevance categories, student count tracking
- Comprehensive statistics and analytics
- Through-models for flexible many-to-many relationships

## Core Data Models (V2)

### Course
- Basic academic course with name, description, ECTS, SWS
- Categorized by `CourseType` (Vorlesung, Übung, Seminar, etc.)
- Classified by `Discipline` (Physische Geographie, Humangeographie, etc.)
- LPO relevance categories via many-to-many relationship
- Sharing functionality between users

### Module
- Collection of courses with ordering and semester assignment
- Through-model `CourseModule` handles course-to-module relationships
- Calculates total ECTS/SWS and provides statistics methods

### Programme
- Collection of modules for specific programme types (Bachelor, Master, Lehramt)
- Through-model `ProgrammeModule` handles module ordering
- Supports student count tracking via `ProgrammeStudentCount`
- Comprehensive statistics methods for ECTS/SWS breakdowns

### Revision
- Snapshot of programmes at a specific point in time
- Contains one programme per programme type
- Provides aggregate statistics across all programmes
- Supports completeness validation

## URL Structure

- **V1**: Root level (`/`, `/programmes/`, `/programme/<id>/`)
- **V2**: Under `/v2/` prefix (`/v2/programmes/`, `/v2/revisions/`, etc.)
- **Admin**: `/admin/` for Django admin interface

## Key Features

### Drag-and-Drop Interface
- Course ordering within modules
- Module ordering within programmes
- AJAX-based updates with proper error handling

### Statistics and Analytics
- ECTS/SWS breakdowns by course type, discipline, and LPO category
- Student count-based class calculation
- Semester-based analysis with winter/summer breakdowns

### User Management
- Built-in Django authentication
- Per-user programme ownership
- Course sharing between users

## Database Configuration

- **Development**: SQLite (`db.sqlite3`)
- **Production**: Configured via `DATABASES` setting
- **Migrations**: Located in `<app>/migrations/`

## Static Files

- **Development**: Served from `static/` directories
- **Production**: Collected to `STATIC_ROOT` via `collectstatic`
- **URL prefix**: `/programme-designer/static/`

## Template Structure

- **V1**: Simple templates in `studyprogrammes/templates/`
- **V2**: More complex templates with includes in `studyprogrammes_v2/templates/`
- **Base template**: `base.html` with common layout
- **Modular components**: Extensive use of template includes

## Testing

- Standard Django test framework
- Test files: `studyprogrammes/tests.py`, `studyprogrammes_v2/tests.py`
- Run with: `python manage.py test`

## Development Notes

- The application uses a multi-app structure to separate legacy (V1) and current (V2) functionality
- V2 represents a significant architectural evolution with more sophisticated domain modeling
- The codebase includes comprehensive through-models for flexible many-to-many relationships
- Statistics methods are heavily used throughout for generating reports and analytics
- The application is designed for deployment with URL prefix `/programme-designer/`