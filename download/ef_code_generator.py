"""
Entity Framework Code Generator Module

This module generates C# Entity Framework Core code from database schema information.
"""

import re
import os
import json
from io import BytesIO, StringIO
import zipfile
import streamlit as st

# C# type mapping for SQL Server types
SQL_TO_CSHARP_TYPE_MAP = {
    'int': 'int',
    'bigint': 'long',
    'smallint': 'short',
    'tinyint': 'byte',
    'bit': 'bool',
    'decimal': 'decimal',
    'numeric': 'decimal',
    'money': 'decimal',
    'smallmoney': 'decimal',
    'float': 'double',
    'real': 'float',
    'datetime': 'DateTime',
    'datetime2': 'DateTime',
    'smalldatetime': 'DateTime',
    'date': 'DateTime',
    'time': 'TimeSpan',
    'datetimeoffset': 'DateTimeOffset',
    'char': 'string',
    'varchar': 'string',
    'text': 'string',
    'nchar': 'string',
    'nvarchar': 'string',
    'ntext': 'string',
    'binary': 'byte[]',
    'varbinary': 'byte[]',
    'image': 'byte[]',
    'uniqueidentifier': 'Guid',
    'xml': 'string',
    'geography': 'Microsoft.SqlServer.Types.SqlGeography',
    'geometry': 'Microsoft.SqlServer.Types.SqlGeometry',
    'hierarchyid': 'Microsoft.SqlServer.Types.SqlHierarchyId',
    'sql_variant': 'object'
}

def clean_name(name):
    """
    Clean a name for use as a C# identifier
    
    Args:
        name: The name to clean
        
    Returns:
        str: Cleaned name
    """
    # Remove invalid characters
    cleaned = re.sub(r'[^\w]', '', name)
    
    # Ensure the name starts with a letter
    if not cleaned[0].isalpha():
        cleaned = 'X' + cleaned
    
    return cleaned

def pascal_case(name):
    """
    Convert a name to PascalCase
    
    Args:
        name: The name to convert
        
    Returns:
        str: PascalCase name
    """
    # Split by non-alphanumeric characters and underscores
    words = re.split(r'[^a-zA-Z0-9]|_', name)
    # Capitalize each word and join
    return ''.join(word.capitalize() for word in words if word)

def camel_case(name):
    """
    Convert a name to camelCase
    
    Args:
        name: The name to convert
        
    Returns:
        str: camelCase name
    """
    pascal = pascal_case(name)
    if pascal:
        return pascal[0].lower() + pascal[1:]
    return pascal

def get_csharp_type(sql_type):
    """
    Convert SQL type to C# type
    
    Args:
        sql_type: SQL type as string
        
    Returns:
        str: Corresponding C# type
    """
    # Extract the base type (remove precision, scale, etc.)
    base_type = sql_type.split('(')[0].lower()
    
    # Look up in the mapping
    return SQL_TO_CSHARP_TYPE_MAP.get(base_type, 'object')

def generate_entity_class(table_name, columns, primary_keys, foreign_keys):
    """
    Generate a C# entity class for a table
    
    Args:
        table_name: Name of the table
        columns: List of column details
        primary_keys: List of primary key column names
        foreign_keys: List of foreign key details
        
    Returns:
        str: C# entity class code
    """
    class_name = pascal_case(table_name)
    
    # Start building the class
    code = f"""using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace YourNamespace.Models
{{
    [Table("{table_name}")]
    public class {class_name}
    {{
"""
    
    # Add properties for each column
    for column in columns:
        col_name = column['name']
        col_type = get_csharp_type(str(column['type']))
        
        # Make nullable if the column is nullable
        if column.get('nullable', True) and col_type not in ['string', 'byte[]', 'object']:
            col_type += '?'
        
        prop_name = pascal_case(col_name)
        
        # Add attributes
        attributes = []
        
        # Primary key attribute
        if col_name in primary_keys:
            attributes.append('[Key]')
            
            # If there are multiple primary keys, add column order
            if len(primary_keys) > 1:
                order = primary_keys.index(col_name)
                attributes.append(f'[Column(Order = {order})]')
        
        # Column name attribute if different from property name
        if col_name != prop_name and col_name != camel_case(prop_name):
            attributes.append(f'[Column("{col_name}")]')
        
        # Required attribute for non-nullable columns
        if not column.get('nullable', True) and col_type not in ['byte[]', 'object']:
            attributes.append('[Required]')
        
        # String length for varchar columns
        if 'varchar' in str(column['type']).lower() or 'nvarchar' in str(column['type']).lower():
            # Extract length if specified
            match = re.search(r'\((\d+)\)', str(column['type']))
            if match and match.group(1) != 'max':
                length = match.group(1)
                attributes.append(f'[StringLength({length})]')
        
        # Add attributes to the code
        for attr in attributes:
            code += f"        {attr}\n"
        
        # Add the property
        code += f"        public {col_type} {prop_name} {{ get; set; }}\n\n"
    
    # Add navigation properties for foreign keys
    for fk in foreign_keys:
        related_table = fk['referred_table']
        related_class = pascal_case(related_table)
        
        prop_name = related_class
        
        # Add navigation property
        code += f"        public virtual {related_class} {prop_name} {{ get; set; }}\n\n"
    
    # Add navigation collections for inverse relationships
    # This requires information about tables that reference this table, which we'll handle separately
    
    # Close the class definition
    code += "    }\n}\n"
    
    return code

def generate_dbcontext_class(schema, context_name="YourDbContext"):
    """
    Generate a C# DbContext class for Entity Framework
    
    Args:
        schema: Full database schema
        context_name: Name of the DbContext class
        
    Returns:
        str: C# DbContext class code
    """
    code = f"""using Microsoft.EntityFrameworkCore;
using YourNamespace.Models;

namespace YourNamespace.Data
{{
    public class {context_name} : DbContext
    {{
        public {context_name}(DbContextOptions<{context_name}> options)
            : base(options)
        {{
        }}

"""
    
    # Add DbSet properties for each table
    for table_name in schema['tables'].keys():
        class_name = pascal_case(table_name)
        dbset_name = pascal_case(table_name) + 's'
        
        code += f"        public DbSet<{class_name}> {dbset_name} {{ get; set; }}\n"
    
    code += "\n        protected override void OnModelCreating(ModelBuilder modelBuilder)\n        {\n"
    
    # Configure relationships
    for rel in schema['relationships']:
        source_table = rel['source_table']
        source_class = pascal_case(source_table)
        source_prop = pascal_case(rel['source_columns'][0]) if rel['source_columns'] else ""
        
        target_table = rel['target_table']
        target_class = pascal_case(target_table)
        target_prop = pascal_case(rel['target_columns'][0]) if rel['target_columns'] else ""
        
        # Skip if we don't have enough information
        if not source_prop or not target_prop:
            continue
            
        # Add relationship configuration
        code += f"""            modelBuilder.Entity<{source_class}>()
                .HasOne(s => s.{target_class})
                .WithMany()
                .HasForeignKey(s => s.{source_prop});

"""
    
    code += "        }\n    }\n}\n"
    
    return code

def generate_entity_configurations(schema):
    """
    Generate Entity Framework configuration classes for all entities
    
    Args:
        schema: Full database schema
        
    Returns:
        dict: Dictionary of entity configuration classes
    """
    configurations = {}
    
    for table_name, table_info in schema['tables'].items():
        class_name = pascal_case(table_name)
        config_class_name = f"{class_name}Configuration"
        
        code = f"""using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using YourNamespace.Models;

namespace YourNamespace.Data.Configurations
{{
    public class {config_class_name} : IEntityTypeConfiguration<{class_name}>
    {{
        public void Configure(EntityTypeBuilder<{class_name}> builder)
        {{
            builder.ToTable("{table_name}");

"""
        
        # Configure primary key
        primary_keys = table_info['primary_keys']
        if primary_keys:
            if len(primary_keys) == 1:
                pk_prop = pascal_case(primary_keys[0])
                code += f"            builder.HasKey(e => e.{pk_prop});\n\n"
            else:
                pk_props = ", ".join(f"e.{pascal_case(pk)}" for pk in primary_keys)
                code += f"            builder.HasKey(e => new {{ {pk_props} }});\n\n"
        
        # Configure columns
        for column in table_info['columns']:
            col_name = column['name']
            prop_name = pascal_case(col_name)
            
            code += f"            builder.Property(e => e.{prop_name})\n"
            code += f"                .HasColumnName(\"{col_name}\")"
            
            # Set column type if available
            if 'type' in column:
                sql_type = str(column['type'])
                code += f"\n                .HasColumnType(\"{sql_type}\")"
            
            # Set nullability
            if not column.get('nullable', True):
                code += "\n                .IsRequired()"
            
            # Set default value if available
            if 'default' in column:
                default_value = column['default']
                code += f"\n                .HasDefaultValue({default_value})"
            
            code += ";\n\n"
        
        # Configure relationships
        for fk in table_info['foreign_keys']:
            ref_table = fk['referred_table']
            ref_class = pascal_case(ref_table)
            
            source_cols = [pascal_case(col) for col in fk['constrained_columns']]
            target_cols = [pascal_case(col) for col in fk['referred_columns']]
            
            if not source_cols or not target_cols:
                continue
                
            nav_prop = ref_class
            
            code += f"            builder.HasOne(e => e.{nav_prop})\n"
            code += "                .WithMany()\n"
            
            if len(source_cols) == 1:
                code += f"                .HasForeignKey(e => e.{source_cols[0]})"
            else:
                fk_props = ", ".join(f"e.{col}" for col in source_cols)
                code += f"                .HasForeignKey(e => new {{ {fk_props} }})"
            
            # Add delete behavior if needed
            # code += "\n                .OnDelete(DeleteBehavior.Cascade)"
            
            code += ";\n\n"
        
        code += "        }\n    }\n}\n"
        
        configurations[config_class_name] = code
    
    return configurations

def generate_startup_code():
    """
    Generate ASP.NET Core startup code for Entity Framework
    
    Returns:
        str: Startup configuration code snippet
    """
    code = """// Add these sections to your Startup.cs or Program.cs file

// Service registration
services.AddDbContext<YourDbContext>(options =>
    options.UseSqlServer(Configuration.GetConnectionString("DefaultConnection")));

// Example appsettings.json configuration
/*
{
  "ConnectionStrings": {
    "DefaultConnection": "Server=yourserver;Database=yourdatabase;Trusted_Connection=True;MultipleActiveResultSets=true"
  }
}
*/
"""
    return code

def generate_migrations_commands():
    """
    Generate Entity Framework Core migrations commands
    
    Returns:
        str: EF Core migration commands
    """
    commands = """// Entity Framework Core migrations commands

// Install required packages
dotnet add package Microsoft.EntityFrameworkCore.SqlServer
dotnet add package Microsoft.EntityFrameworkCore.Tools

// Create initial migration
dotnet ef migrations add InitialCreate

// Apply migrations to the database
dotnet ef database update
"""
    return commands

def generate_repository_pattern(schema):
    """
    Generate repository pattern implementation
    
    Args:
        schema: Full database schema
        
    Returns:
        dict: Dictionary of repository interface and implementation classes
    """
    repositories = {}
    
    # Generic repository interface
    repositories["IRepository.cs"] = """using System;
using System.Collections.Generic;
using System.Linq;
using System.Linq.Expressions;
using System.Threading.Tasks;

namespace YourNamespace.Repositories
{
    public interface IRepository<T> where T : class
    {
        // Synchronous methods
        IQueryable<T> GetAll();
        IQueryable<T> Find(Expression<Func<T, bool>> predicate);
        T GetById(object id);
        void Add(T entity);
        void AddRange(IEnumerable<T> entities);
        void Update(T entity);
        void Remove(T entity);
        void RemoveRange(IEnumerable<T> entities);
        
        // Asynchronous methods
        Task<List<T>> GetAllAsync();
        Task<T> GetByIdAsync(object id);
        Task AddAsync(T entity);
        Task AddRangeAsync(IEnumerable<T> entities);
    }
}
"""
    
    # Generic repository implementation
    repositories["Repository.cs"] = """using Microsoft.EntityFrameworkCore;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Linq.Expressions;
using System.Threading.Tasks;
using YourNamespace.Data;

namespace YourNamespace.Repositories
{
    public class Repository<T> : IRepository<T> where T : class
    {
        protected readonly YourDbContext _context;
        protected readonly DbSet<T> _dbSet;

        public Repository(YourDbContext context)
        {
            _context = context;
            _dbSet = context.Set<T>();
        }

        public virtual IQueryable<T> GetAll()
        {
            return _dbSet;
        }

        public virtual IQueryable<T> Find(Expression<Func<T, bool>> predicate)
        {
            return _dbSet.Where(predicate);
        }

        public virtual T GetById(object id)
        {
            return _dbSet.Find(id);
        }

        public virtual void Add(T entity)
        {
            _dbSet.Add(entity);
        }

        public virtual void AddRange(IEnumerable<T> entities)
        {
            _dbSet.AddRange(entities);
        }

        public virtual void Update(T entity)
        {
            _dbSet.Attach(entity);
            _context.Entry(entity).State = EntityState.Modified;
        }

        public virtual void Remove(T entity)
        {
            if (_context.Entry(entity).State == EntityState.Detached)
            {
                _dbSet.Attach(entity);
            }
            _dbSet.Remove(entity);
        }

        public virtual void RemoveRange(IEnumerable<T> entities)
        {
            _dbSet.RemoveRange(entities);
        }

        public virtual async Task<List<T>> GetAllAsync()
        {
            return await _dbSet.ToListAsync();
        }

        public virtual async Task<T> GetByIdAsync(object id)
        {
            return await _dbSet.FindAsync(id);
        }

        public virtual async Task AddAsync(T entity)
        {
            await _dbSet.AddAsync(entity);
        }

        public virtual async Task AddRangeAsync(IEnumerable<T> entities)
        {
            await _dbSet.AddRangeAsync(entities);
        }
    }
}
"""
    
    # Unit of work interface
    repositories["IUnitOfWork.cs"] = """using System;
using System.Threading.Tasks;

namespace YourNamespace.Repositories
{
    public interface IUnitOfWork : IDisposable
    {
        // Add specific repositories here
"""
    
    # Add repository properties for each entity
    for table_name in schema['tables'].keys():
        class_name = pascal_case(table_name)
        prop_name = f"{class_name}Repository"
        
        repositories["IUnitOfWork.cs"] += f"        IRepository<{class_name}> {prop_name} {{ get; }}\n"
    
    repositories["IUnitOfWork.cs"] += """
        // Save changes methods
        int Complete();
        Task<int> CompleteAsync();
    }
}
"""
    
    # Unit of work implementation
    repositories["UnitOfWork.cs"] = """using System;
using System.Threading.Tasks;
using YourNamespace.Data;
using YourNamespace.Models;

namespace YourNamespace.Repositories
{
    public class UnitOfWork : IUnitOfWork
    {
        private readonly YourDbContext _context;
        private bool _disposed = false;

"""
    
    # Add repository field declarations
    for table_name in schema['tables'].keys():
        class_name = pascal_case(table_name)
        field_name = f"_{camel_case(table_name)}Repository"
        prop_name = f"{class_name}Repository"
        
        repositories["UnitOfWork.cs"] += f"        private IRepository<{class_name}> {field_name};\n"
    
    repositories["UnitOfWork.cs"] += """
        public UnitOfWork(YourDbContext context)
        {
            _context = context;
        }

"""
    
    # Add repository property implementations
    for table_name in schema['tables'].keys():
        class_name = pascal_case(table_name)
        field_name = f"_{camel_case(table_name)}Repository"
        prop_name = f"{class_name}Repository"
        
        repositories["UnitOfWork.cs"] += f"""        public IRepository<{class_name}> {prop_name}
        {{
            get
            {{
                if ({field_name} == null)
                {{
                    {field_name} = new Repository<{class_name}>(_context);
                }}
                return {field_name};
            }}
        }}

"""
    
    # Add rest of the UnitOfWork implementation
    repositories["UnitOfWork.cs"] += """        public int Complete()
        {
            return _context.SaveChanges();
        }

        public async Task<int> CompleteAsync()
        {
            return await _context.SaveChangesAsync();
        }

        protected virtual void Dispose(bool disposing)
        {
            if (!_disposed)
            {
                if (disposing)
                {
                    _context.Dispose();
                }
            }
            _disposed = true;
        }

        public void Dispose()
        {
            Dispose(true);
            GC.SuppressFinalize(this);
        }
    }
}
"""
    
    return repositories

def generate_service_layer(schema):
    """
    Generate service layer implementation
    
    Args:
        schema: Full database schema
        
    Returns:
        dict: Dictionary of service interface and implementation classes
    """
    services = {}
    
    # Generate generic service interface
    services["IService.cs"] = """using System;
using System.Collections.Generic;
using System.Linq;
using System.Linq.Expressions;
using System.Threading.Tasks;

namespace YourNamespace.Services
{
    public interface IService<T> where T : class
    {
        IQueryable<T> GetAll();
        IEnumerable<T> Find(Expression<Func<T, bool>> predicate);
        T GetById(object id);
        void Add(T entity);
        void AddRange(IEnumerable<T> entities);
        void Update(T entity);
        void Remove(T entity);
        void RemoveRange(IEnumerable<T> entities);
        void SaveChanges();
        
        // Async methods
        Task<List<T>> GetAllAsync();
        Task<T> GetByIdAsync(object id);
        Task AddAsync(T entity);
        Task AddRangeAsync(IEnumerable<T> entities);
        Task SaveChangesAsync();
    }
}
"""
    
    # Generate generic service implementation
    services["Service.cs"] = """using System;
using System.Collections.Generic;
using System.Linq;
using System.Linq.Expressions;
using System.Threading.Tasks;
using YourNamespace.Repositories;

namespace YourNamespace.Services
{
    public class Service<T> : IService<T> where T : class
    {
        protected readonly IUnitOfWork _unitOfWork;
        protected readonly IRepository<T> _repository;

        public Service(IUnitOfWork unitOfWork, IRepository<T> repository)
        {
            _unitOfWork = unitOfWork;
            _repository = repository;
        }

        public virtual IQueryable<T> GetAll()
        {
            return _repository.GetAll();
        }

        public virtual IEnumerable<T> Find(Expression<Func<T, bool>> predicate)
        {
            return _repository.Find(predicate);
        }

        public virtual T GetById(object id)
        {
            return _repository.GetById(id);
        }

        public virtual void Add(T entity)
        {
            _repository.Add(entity);
        }

        public virtual void AddRange(IEnumerable<T> entities)
        {
            _repository.AddRange(entities);
        }

        public virtual void Update(T entity)
        {
            _repository.Update(entity);
        }

        public virtual void Remove(T entity)
        {
            _repository.Remove(entity);
        }

        public virtual void RemoveRange(IEnumerable<T> entities)
        {
            _repository.RemoveRange(entities);
        }

        public virtual void SaveChanges()
        {
            _unitOfWork.Complete();
        }

        public virtual async Task<List<T>> GetAllAsync()
        {
            return await _repository.GetAllAsync();
        }

        public virtual async Task<T> GetByIdAsync(object id)
        {
            return await _repository.GetByIdAsync(id);
        }

        public virtual async Task AddAsync(T entity)
        {
            await _repository.AddAsync(entity);
        }

        public virtual async Task AddRangeAsync(IEnumerable<T> entities)
        {
            await _repository.AddRangeAsync(entities);
        }

        public virtual async Task SaveChangesAsync()
        {
            await _unitOfWork.CompleteAsync();
        }
    }
}
"""
    
    # Generate specific service interfaces and implementations for each entity
    for table_name in schema['tables'].keys():
        class_name = pascal_case(table_name)
        service_interface_name = f"I{class_name}Service"
        service_class_name = f"{class_name}Service"
        
        # Service interface
        services[f"{service_interface_name}.cs"] = f"""using System.Collections.Generic;
using System.Threading.Tasks;
using YourNamespace.Models;

namespace YourNamespace.Services
{{
    public interface {service_interface_name} : IService<{class_name}>
    {{
        // Add specific methods for {class_name} here
    }}
}}
"""
        
        # Service implementation
        services[f"{service_class_name}.cs"] = f"""using System.Collections.Generic;
using System.Threading.Tasks;
using YourNamespace.Models;
using YourNamespace.Repositories;

namespace YourNamespace.Services
{{
    public class {service_class_name} : Service<{class_name}>, {service_interface_name}
    {{
        public {service_class_name}(IUnitOfWork unitOfWork) 
            : base(unitOfWork, unitOfWork.{class_name}Repository)
        {{
        }}

        // Implement specific methods for {class_name} here
    }}
}}
"""
    
    return services

def generate_ef_code(schema):
    """
    Generate Entity Framework code files from database schema
    
    Args:
        schema: Full database schema
        
    Returns:
        dict: Dictionary of generated code files
    """
    code_files = {}
    
    # Generate entity classes
    for table_name, table_info in schema['tables'].items():
        class_name = pascal_case(table_name)
        code = generate_entity_class(
            table_name,
            table_info['columns'],
            table_info['primary_keys'],
            table_info['foreign_keys']
        )
        code_files[f"Models/{class_name}.cs"] = code
    
    # Generate DbContext
    code_files["Data/YourDbContext.cs"] = generate_dbcontext_class(schema)
    
    # Generate entity configurations
    entity_configs = generate_entity_configurations(schema)
    for config_name, config_code in entity_configs.items():
        code_files[f"Data/Configurations/{config_name}.cs"] = config_code
    
    # Generate startup code
    code_files["Startup_EF_Config.cs"] = generate_startup_code()
    
    # Generate migrations commands
    code_files["EF_Migrations_Commands.txt"] = generate_migrations_commands()
    
    # Generate repository pattern implementation
    repositories = generate_repository_pattern(schema)
    for repo_name, repo_code in repositories.items():
        code_files[f"Repositories/{repo_name}"] = repo_code
    
    # Generate service layer
    services = generate_service_layer(schema)
    for service_name, service_code in services.items():
        code_files[f"Services/{service_name}"] = service_code
    
    return code_files

def create_code_zip(code_files):
    """
    Create a ZIP file with generated code files
    
    Args:
        code_files: Dictionary of file paths and their content
        
    Returns:
        BytesIO: ZIP file as a bytes buffer
    """
    zip_buffer = BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for file_path, content in code_files.items():
            zip_file.writestr(file_path, content)
    
    zip_buffer.seek(0)
    return zip_buffer

def display_code_preview(code_files):
    """
    Display a preview of generated code files in Streamlit
    
    Args:
        code_files: Dictionary of file paths and their content
    """
    st.subheader("Generated Code Preview")
    
    # Get a list of file paths
    file_paths = list(code_files.keys())
    file_paths.sort()
    
    # Create tabs for different code categories
    tab_models, tab_context, tab_repo, tab_service = st.tabs(["Models", "DbContext", "Repositories", "Services"])
    
    with tab_models:
        st.write("Entity model classes for your database tables:")
        model_files = [path for path in file_paths if path.startswith("Models/")]
        if model_files:
            selected_model = st.selectbox("Select a model class:", model_files)
            st.code(code_files[selected_model], language="csharp")
        else:
            st.info("No model files generated.")
    
    with tab_context:
        st.write("Database context and configuration:")
        context_files = [path for path in file_paths if path.startswith("Data/")]
        if context_files:
            selected_context = st.selectbox("Select a context file:", context_files)
            st.code(code_files[selected_context], language="csharp")
        else:
            st.info("No context files generated.")
    
    with tab_repo:
        st.write("Repository pattern implementation:")
        repo_files = [path for path in file_paths if path.startswith("Repositories/")]
        if repo_files:
            selected_repo = st.selectbox("Select a repository file:", repo_files)
            st.code(code_files[selected_repo], language="csharp")
        else:
            st.info("No repository files generated.")
    
    with tab_service:
        st.write("Service layer implementation:")
        service_files = [path for path in file_paths if path.startswith("Services/")]
        if service_files:
            selected_service = st.selectbox("Select a service file:", service_files)
            st.code(code_files[selected_service], language="csharp")
        else:
            st.info("No service files generated.")
    
    # Add download button for the ZIP file
    zip_buffer = create_code_zip(code_files)
    st.download_button(
        label="Download All Code Files",
        data=zip_buffer,
        file_name="entity_framework_code.zip",
        mime="application/zip"
    )