#!/usr/bin/env python3
"""
Asset Management System - Entry Point
Run this file to start the Flask application.
"""

from app import create_app

app = create_app()

if __name__ == '__main__':
    print("=" * 60)
    print("  ASSET MANAGEMENT SYSTEM")
    print("=" * 60)
    print("\nStarting server...")
    print("Open your browser and go to: http://127.0.0.1:5000")
    print("\nAdmin Login Credentials:")
    print("  Username: admin")
    print("  Password: 123456")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)