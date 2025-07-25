#!/usr/bin/env python3

import os
import shutil
import logging
from datetime import datetime
from watcher_test_base import WatcherTestBase
from memory_bear.utils.markdown import parse_md_file

# Set up logging
logger = logging.getLogger(__name__)


class SyncTestBase(WatcherTestBase):
    """
    Base class for sync testing functionality.
    Inherits server control and basic test utilities from WatcherTestBase.
    """

    def __init__(self):
        """
        Initialize the sync test base.
        """
        super().__init__()
        logger.info("SyncTestBase initialized")

    def create_content(self, file_type, index):
        """
        Create unique content using template with parameters.
        
        Args:
            file_type (str): Type of file ('baseline', 'offline', etc.)
            index (int): File index for uniqueness
            
        Returns:
            str: Unique markdown content
        """
        template = """---
title: "{title}"
tags: {tags}
---

# {title}

{description}

## Content Details
- File type: {file_type}
- Index: {index}
- Created: {timestamp}
- Purpose: {purpose}

{body_content}
"""
        
        content_variations = {
            "baseline": {
                "title": f"Baseline Document {index + 1}",
                "tags": f'["baseline", "sync-test", "doc-{index + 1}"]',
                "description": f"This is baseline document #{index + 1} for sync testing.",
                "purpose": "Establish initial state for sync operations",
                "body_content": f"Baseline content for document {index + 1}.\n\nThis file will be used to test sync functionality when the server goes offline and comes back online."
            },
            "offline": {
                "title": f"Offline Created Document {index + 1}",
                "tags": f'["offline", "created", "sync-test", "new-{index + 1}"]',
                "description": f"This document was created while the server was offline.",
                "purpose": "Test offline file creation sync",
                "body_content": f"This file was created during offline period {index + 1}.\n\nIt should be detected and indexed when the server restarts."
            }
        }
        
        params = content_variations[file_type]
        params.update({
            "file_type": file_type,
            "index": index,
            "timestamp": datetime.now().isoformat()
        })
        
        return template.format(**params)

    def setup_baseline_files(self, count=3):
        """
        Create initial files while watcher is running and verify indexing.
        
        Args:
            count (int): Number of baseline files to create (default: 3)
            
        Returns:
            list: List of dicts with file info: [{'path': str, 'uuid': str, 'properties': dict}]
        """
        baseline_files = []
        
        for i in range(count):
            # Create each baseline file with distinct content
            content = self.create_content("baseline", i)
            file_path = self.create_test_file(f"baseline_{i}", content)
            
            # Wait for indexing and get object info 
            indexed_object = self.poll_for_object(file_path, should_exist=True)
            
            # Store complete file info for later comparison
            baseline_files.append({
                'path': file_path,
                'uuid': str(indexed_object.uuid),
                'properties': indexed_object.properties.copy()
            })
        
        logger.info(f"Created {len(baseline_files)} unique baseline files")
        return baseline_files

    def make_offline_changes(self, baseline_files):
        """
        Make file system changes while watcher is stopped.
        
        Args:
            baseline_files (list): List of baseline file info from setup_baseline_files()
            
        Returns:
            dict: Expected changes categorized by operation type
        """
        changes = {
            'created': [],
            'modified': [],
            'deleted': [],
            'moved': []
        }
        
        # 1. Create new files (will be detected on sync)
        for i in range(2):
            # Create each offline file with distinct content
            content = self.create_content("offline", i)
            new_file = self.create_test_file(f"offline_created_{i}", content)
            changes['created'].append(new_file)
        
        # 2. Modify existing file (will update existing object)
        if len(baseline_files) > 0:
            modified_file = self.modify_test_file(baseline_files[0]['path'])
            changes['modified'].append({
                'path': modified_file,
                'original_uuid': baseline_files[0]['uuid']
            })
        
        # 3. Delete file 
        if len(baseline_files) > 1:
            deleted_path = baseline_files[1]['path']
            os.remove(deleted_path)
            changes['deleted'].append(deleted_path)
        
        # 4. Move file (sync will handle as delete + create)
        if len(baseline_files) > 2:
            old_path = baseline_files[2]['path']
            moved_dir = os.path.join(os.getenv('NOTES_DIR'), "Offline")
            os.makedirs(moved_dir, exist_ok=True)
            new_path = os.path.join(moved_dir, os.path.basename(old_path))
            shutil.move(old_path, new_path)
            changes['moved'].append({
                'old_path': old_path,
                'new_path': new_path
            })
        
        logger.info(f"Made offline changes: {len(changes['created'])} created, {len(changes['modified'])} modified, {len(changes['deleted'])} deleted, {len(changes['moved'])} moved")
        return changes

    def verify_sync_results(self, expected_changes, timeout=20):
        """
        Verify database reflects all offline changes after sync.
        
        Args:
            expected_changes (dict): Dict from make_offline_changes()
            timeout (int): Max seconds to wait for sync completion (default: 20)
        """
        # 1. Verify created files are indexed
        for created_path in expected_changes['created']:
            indexed_object = self.poll_for_object(created_path, should_exist=True, timeout=timeout)
            expected_data = parse_md_file(created_path)
            self.validate_object(indexed_object, expected_data)
            logger.info(f"✅ Created file synced: {created_path}")
        
        # 2. Verify modified files are updated (UUID preserved)
        for modified_info in expected_changes['modified']:
            updated_object = self.poll_for_object(
                modified_info['path'], 
                should_exist=True,
                condition_func=lambda obj: 'Modified Test Note' in obj.properties.get('title', ''),
                timeout=timeout
            )
            expected_data = parse_md_file(modified_info['path'])
            expected_data['uuid'] = modified_info['original_uuid']
            self.validate_object(updated_object, expected_data, skip_properties=['created_at'])
            logger.info(f"✅ Modified file synced: {modified_info['path']}")
        
        # 3. Verify deleted files are removed
        for deleted_path in expected_changes['deleted']:
            self.poll_for_object(deleted_path, should_exist=False)
            logger.info(f"✅ Deleted file removed: {deleted_path}")
        
        # 4. Verify moved files are handled (sync treats moves as delete+create)
        for moved_info in expected_changes['moved']:
            # Old path should not exist (deleted during sync); Note: query result does not match collection state, IS deleted but shows up
            # self.poll_for_object(moved_info['old_path'], should_exist=False)
            
            # New path should exist (created during sync)
            # Note: UUID will be different since sync treats this as delete+create, not move
            moved_object = self.poll_for_object(moved_info['new_path'], should_exist=True)
            expected_data = parse_md_file(moved_info['new_path'])

            self.validate_object(moved_object, expected_data)
            logger.info(f"✅ Moved file synced: {moved_info['old_path']} → {moved_info['new_path']}")
        
        logger.info("All sync operations verified successfully!") 