from setuptools import setup, find_packages

setup(
    name='eyedeea_photos_stream_server',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'Flask',
        'selenium',
        'opencv-python',
        'python-dotenv',
    ],
    entry_points={
        'console_scripts': [
            'stream-server=stream_server.main:main',
        ],
    },
    include_package_data=True,
    description='Eyedeea Photos streaming server for google chromecast',
    author='eyediatech',
    author_email='support@eyediatech.com',
)
