from setuptools import setup, find_packages
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# Implements parse_requirements as standalone functionality
with open("requirements.txt") as f:
    reqs = [l.strip('\n') for l in f if l.strip('\n') and not l.startswith('#')]

setup(
    name='blastradius',
    version='0.1.25.1',
    description='Interactive Terraform graph visualizations',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='Patrick McMurchie',
    author_email='patrick.mcmurchie@gmail.com',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    scripts=['bin/blast-radius'],
    install_requires=reqs,
    data_files=[('blastradius/server/templates', ['blastradius/server/templates/error.html', 'blastradius/server/templates/index.html']),
                  ('blastradius/server/static/images',['blastradius/server/static/images/controls.png','blastradius/server/static/images/apply.png','blastradius/server/static/images/correct.png','blastradius/server/static/images/instance.png','blastradius/server/static/images/plan.png','blastradius/server/static/images/vpc.png','blastradius/server/static/images/instance.png','blastradius/server/static/images/cost.png','blastradius/server/static/images/time.png','blastradius/server/static/images/policy.png','blastradius/server/static/images/error.png','blastradius/server/static/images/hourglass.png','blastradius/server/static/images/kp.png','blastradius/server/static/images/COS_Icon.png','blastradius/server/static/images/kubernetes.png','blastradius/server/static/images/resource.png']),
                 ('blastradius/server/static/css', ['blastradius/server/static/css/bootstrap.min.css', 'blastradius/server/static/css/selectize.css','blastradius/server/static/css/style.css']),
                 ('blastradius/server/static/js', ['blastradius/server/static/js/blast-radius.js', 'blastradius/server/static/js/bootstrap.min.js','blastradius/server/static/js/categories.js','blastradius/server/static/js/d3-tip.js','blastradius/server/static/js/d3.v4.js','blastradius/server/static/js/d3.v4.min.js','blastradius/server/static/js/fontawesome-all.min.js','blastradius/server/static/js/jquery.slim.min.js','blastradius/server/static/js/selectize.js','blastradius/server/static/js/svg-pan-zoom.js','blastradius/server/static/js/json2yaml.js']), ],
)