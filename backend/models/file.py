from datetime import datetime
import os
from app.database.database import db

class File(db.Model):
    __tablename__ = 'files'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    filename = db.Column(db.String(255), nullable=False)
    s3_key = db.Column(db.String(500), nullable=False, unique=True)
    file_size = db.Column(db.BigInteger, nullable=False)
    content_type = db.Column(db.String(100), nullable=True)
    folder_path = db.Column(db.String(500), nullable=True, default='')  # Folder path like 'documents/2024/'
    is_folder = db.Column(db.Boolean, default=False, nullable=False)  # True for folders, False for files
    parent_folder_id = db.Column(db.Integer, db.ForeignKey('files.id'), nullable=True)  # For folder hierarchy
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    parent_folder = db.relationship('File', remote_side=[id], backref='children')
    
    # Indexes for better query performance
    __table_args__ = (
        db.Index('idx_user_uploaded', 'user_id', 'uploaded_at'),
        db.Index('idx_filename', 'filename'),
        db.Index('idx_folder_path', 'folder_path'),
        db.Index('idx_parent_folder', 'parent_folder_id'),
    )
    
    def __repr__(self):
        return f'<File {self.filename}>'
    
    def get_file_extension(self):
        """Get the file extension"""
        return os.path.splitext(self.filename)[1].lower()
    
    def get_file_size_mb(self):
        """Get file size in MB"""
        return round(float(self.file_size) / (1024 * 1024), 2)
    
    def get_file_size_formatted(self):
        """Get formatted file size string"""
        size = float(self.file_size)  # Convert to float to handle Decimal types
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
    def get_full_path(self):
        """Get the full path including folder"""
        if self.folder_path:
            return f"{self.folder_path}{self.filename}"
        return self.filename
    
    def get_s3_key_with_folder(self):
        """Get S3 key with folder path"""
        if self.folder_path:
            return f"{self.folder_path}{self.filename}"
        return self.filename
    
    def to_dict(self):
        """Convert file to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'filename': self.filename,
            's3_key': self.s3_key,
            'file_size': self.file_size,
            'file_size_formatted': self.get_file_size_formatted(),
            'content_type': self.content_type,
            'folder_path': self.folder_path or '',
            'is_folder': self.is_folder,
            'parent_folder_id': self.parent_folder_id,
            'full_path': self.get_full_path(),
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None,
            'extension': self.get_file_extension()
        }
