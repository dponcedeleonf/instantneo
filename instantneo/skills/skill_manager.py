import sys
import os
import asyncio
import importlib
import importlib.util
import inspect
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Any, Union, Optional, Callable, Tuple

class SkillLoader:
    def __init__(self, manager: "SkillManager"):
        self.manager = manager
    
    def _build_metadata_filter(self, by_tags: Optional[List[str]] = None, by_name: Optional[str] = None) -> Callable[[Dict[str, Any]], bool]:
        def metadata_filter(metadata: Dict[str, Any]) -> bool:
            if by_tags and not all(tag in metadata.get('tags', []) for tag in by_tags):
                return False
            if by_name and metadata.get('name') != by_name:
                return False
            return True
        return metadata_filter
    
    def from_file(self, file_path: str, by_tags: Optional[List[str]] = None, by_name: Optional[str] = None) -> List[str]:
        metadata_filter = self._build_metadata_filter(by_tags, by_name)
        return self.manager._load_skills_from_file(file_path, metadata_filter)

    def from_folder(self, folder_path: str, by_tags: Optional[List[str]] = None, by_name: Optional[str] = None) -> List[str]:
        metadata_filter = self._build_metadata_filter(by_tags, by_name)
        return self.manager._load_skills_from_folder(folder_path, metadata_filter)

    def from_current(self, by_tags: Optional[List[str]] = None, by_name: Optional[str] = None) -> None:
        metadata_filter = self._build_metadata_filter(by_tags, by_name)
        self.manager._load_skills_from_current_module(metadata_filter)

    def from_module(self, module: Any, by_tags: Optional[List[str]] = None, by_name: Optional[str] = None) -> None:
        metadata_filter = self._build_metadata_filter(by_tags, by_name)
        self.manager._load_skills_from_module(module, metadata_filter)

class SkillManager:
    def __init__(self):
        # Store the context module in which the manager was instantiated
        caller_frame = inspect.currentframe().f_back
        self.instantiation_module = inspect.getmodule(caller_frame)

        self.registry: Dict[str, Any] = {}
        self.registry_by_name: Dict[str, List[Any]] = {}
        self.duplicates: Dict[str, List[Any]] = {}
        # Instantiate the auxiliary class for loading skills
        self.load_skills = SkillLoader(self)


    def register_skill(self, func) -> None:
        
        key = f"{func.__module__}.{func.__name__}"
        simple_name = func.__name__
        file_path = func.__code__.co_filename

        if simple_name in self.registry_by_name:
            if simple_name not in self.duplicates:
                self.duplicates[simple_name] = []
            self.duplicates[simple_name].append(func)
            print(f"Warning: The skill '{simple_name}' was already registered in  "
                  f"{self.registry_by_name[simple_name][0].__code__.co_filename}. "
                  f"The definition in {file_path} has been added to the duplicates registry.")
        else:
            self.registry_by_name[simple_name] = [func]

        self.registry[key] = func

    def _load_skills_from_module(self, module, 
                                      metadata_filter: Optional[Callable[[Dict[str, Any]], bool]] = None) -> None:
       
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if callable(attr) and hasattr(attr, 'skill_metadata'):
                if metadata_filter is not None:
                    if not metadata_filter(attr.skill_metadata):
                        continue
                self.register_skill(attr)

    def _load_skills_from_current_module(
        self, 
        metadata_filter: Optional[Callable[[Dict[str, Any]], bool]] = None
    ) -> None:
        # We directly use the module stored in the constructor
        caller_module = self.instantiation_module
        if caller_module:
            self._load_skills_from_module(caller_module, metadata_filter)
        else:
            raise RuntimeError("Could not determine the module that instantiated SkillManager.")

    def _load_skills_from_file(self, file_path: str, 
                         metadata_filter: Optional[Callable[[Dict[str, Any]], bool]] = None) -> List[str]:
        if not os.path.isfile(file_path):
            raise ValueError(f"{file_path} is not a valid file.")
        
        try:
            module_name = os.path.splitext(os.path.basename(file_path))[0]
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            
            if spec is None or spec.loader is None:
                raise ImportError(f"Could not create a spec for {file_path}")
                
            module = importlib.util.module_from_spec(spec)
            
            # Temporarily set up sys.modules to handle possible relative imports
            sys.modules[module_name] = module
            
            try:
                spec.loader.exec_module(module)
            except Exception as e:
                raise ImportError(f"Error executing module: {str(e)}")

            registered = []
            try:
                self._load_skills_from_module(module, metadata_filter)
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if callable(attr) and hasattr(attr, 'skill_metadata'):
                        skill_id = f"{module_name}.{attr.__name__}"
                        registered.append(skill_id)
            except Exception as e:
                raise ValueError(f"Error processing skills in module: {str(e)}")
                
            return registered
            
        except Exception as e:
            # Capture and forward the exception with clear information
            raise Exception(f"Error loading {os.path.basename(file_path)}: {str(e)}")
        finally:
            # Clean up sys.modules if we added something temporarily
            if module_name in sys.modules and sys.modules[module_name].__file__ == file_path:
                del sys.modules[module_name]

    def _load_skills_from_folder(self, folder_path: str,
                            metadata_filter: Optional[Callable[[Dict[str, Any]], bool]] = None) -> List[str]:
        registered, errors = asyncio.run(self._load_skills_from_folder_async(folder_path, metadata_filter))
        
        # Report errors if any
        if errors:
            error_count = len(errors)
            file_count = len([f for f in os.listdir(folder_path) if f.endswith('.py')])
            print(f"⚠️ {error_count} of {file_count} files could not be loaded properly:")
            for file_name, error in errors.items():
                print(f"  - {file_name}: {error}")
        
        return registered
    async def _load_skills_from_folder_async(self, folder_path: str,
                                         metadata_filter: Optional[Callable[[Dict[str, Any]], bool]] = None) -> Tuple[List[str], Dict[str, str]]:
        if not os.path.isdir(folder_path):
            raise ValueError(f"{folder_path} is not a valid directory.")
        
        # Find all Python files in the folder
        python_files = [
            os.path.join(folder_path, filename)
            for filename in os.listdir(folder_path)
            if filename.endswith('.py')
        ]
        
        # Define an internal function that handles errors
        def load_file_with_error_handling(file_path, metadata_filter):
            try:
                return self._load_skills_from_file(file_path, metadata_filter), None
            except Exception as e:
                error_msg = f"Error loading {os.path.basename(file_path)}: {str(e)}"
                return [], error_msg
        
        # Create tasks to load each file
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=min(os.cpu_count(), 4)) as executor:
            # Convert the synchronous method into asynchronous tasks using ThreadPoolExecutor
            tasks = [
                loop.run_in_executor(
                    executor,
                    load_file_with_error_handling,
                    file_path,
                    metadata_filter
                )
                for file_path in python_files
            ]
            
            # Wait for all tasks to complete
            results = await asyncio.gather(*tasks)
        
        # Combine all results and collect errors
        registered = []
        errors = {}
        
        for i, (skills, error) in enumerate(results):
            if skills:
                registered.extend(skills)
            if error:
                file_name = os.path.basename(python_files[i])
                errors[file_name] = error
                
        return registered, errors
    # Query and registry management methods
    def get_skill_names(self) -> List[str]:
        return list({func.__name__ for func in self.registry.values()})

    def get_skills_with_keys(self) -> Dict[str, Any]:
        return self.registry

    def get_all_skills_metadata(self) -> Dict[str, Dict[str, Any]]:
        return {
            key: {"key": key, **func.skill_metadata}
            for key, func in sorted(self.registry.items())
        }
    
    def get_skill_metadata_by_name(self, name: str) -> Dict[str, Any]:
        matches = {key: func for key, func in self.registry.items() if func.__name__ == name}
        if not matches:
            return None
        if len(matches) == 1:
            return matches[next(iter(matches.keys()))].skill_metadata
        return {key: func.skill_metadata for key, func in matches.items()}

    def get_skills_by_tag(self, tag: str, 
                          return_keys: bool = False) -> Union[List[str], Dict[str, Any]]:
        filtered = {
            key: func for key, func in self.registry.items()
            if tag in func.skill_metadata.get('tags', [])
        }
        if return_keys:
            return filtered
        else:
            return list({func.__name__ for func in filtered.values()})

    def get_skill_by_name(self, name: str) -> Union[Any, Dict[str, Any], None]:
        matches = {key: func for key, func in self.registry.items() if func.__name__ == name}
        if not matches:
            return None
        if len(matches) == 1:
            return next(iter(matches.values()))
        return matches

    def get_duplicate_skills(self) -> Dict[str, List[Any]]:
        return self.duplicates

    def remove_skill(self, name: str, module: Optional[str] = None) -> bool:
        if name not in self.registry_by_name:
            return False

        if module:
            key_to_remove = f"{module}.{name}"
            if key_to_remove in self.registry:
                self.registry.pop(key_to_remove)
                self.registry_by_name[name] = [
                    func for func in self.registry_by_name[name] if func.__module__ != module
                ]
                if not self.registry_by_name[name]:
                    self.registry_by_name.pop(name)
                return True
            else:
                return False
        else:
            if len(self.registry_by_name[name]) == 1:
                func_to_remove = self.registry_by_name[name][0]
                key_to_remove = f"{func_to_remove.__module__}.{name}"
                self.registry.pop(key_to_remove, None)
                self.registry_by_name.pop(name, None)
                return True
            else:
                print(f"Warning: There are multiple skills with the name '{name}'. Please specify the module to remove.")
                return False

    def clear_registry(self) -> None:
        self.registry.clear()
        self.registry_by_name.clear()
        self.duplicates.clear()

    def update_skill_metadata(self, key: str, new_metadata: Dict[str, Any]) -> bool:
        if key in self.registry:
            func = self.registry[key]
            func.skill_metadata.update(new_metadata)
            return True
        return False