from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from studyprogrammes_v2.models import Course, Module, Programme, Revision, CourseType, Discipline, LPO, ProgrammeType


class Command(BaseCommand):
    help = 'Create sample data for testing the V2 application'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample data...')
        
        # Create a user if none exists
        user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'first_name': 'Test',
                'last_name': 'User',
                'email': 'admin@example.com'
            }
        )
        if created:
            user.set_password('admin')
            user.save()
            self.stdout.write('Created admin user')
        
        # Create sample courses
        courses_data = [
            {
                'name': 'Einführung in die Informatik',
                'description': 'Grundlagen der Informatik und Programmierung',
                'semester': 1,
                'course_type': CourseType.VORLESUNG,
                'discipline': Discipline.INFORMATIK,
                'lpo_relevance': LPO.LPO_I,
                'ects': 6,
                'sws': 4,
                'max_participants': 150,
                'order': 1
            },
            {
                'name': 'Mathematik für Informatiker I',
                'description': 'Diskrete Mathematik und Logik',
                'semester': 1,
                'course_type': CourseType.VORLESUNG,
                'discipline': Discipline.MATHEMATIK,
                'lpo_relevance': LPO.LPO_I,
                'ects': 9,
                'sws': 6,
                'max_participants': 120,
                'order': 2
            },
            {
                'name': 'Programmierparadigmen',
                'description': 'Funktionale und objektorientierte Programmierung',
                'semester': 2,
                'course_type': CourseType.VORLESUNG,
                'discipline': Discipline.INFORMATIK,
                'lpo_relevance': LPO.LPO_I,
                'ects': 6,
                'sws': 4,
                'max_participants': 100,
                'order': 3
            },
            {
                'name': 'Algorithmen und Datenstrukturen',
                'description': 'Grundlegende Algorithmen und deren Implementierung',
                'semester': 2,
                'course_type': CourseType.VORLESUNG,
                'discipline': Discipline.INFORMATIK,
                'lpo_relevance': LPO.LPO_I,
                'ects': 9,
                'sws': 6,
                'max_participants': 100,
                'order': 4
            },
            {
                'name': 'Praktikum Programmierung',
                'description': 'Praktische Programmieraufgaben',
                'semester': 1,
                'course_type': CourseType.PRAKTIKUM,
                'discipline': Discipline.INFORMATIK,
                'lpo_relevance': LPO.LPO_I,
                'ects': 3,
                'sws': 2,
                'max_participants': 25,
                'order': 5
            },
            {
                'name': 'Datenbanksysteme',
                'description': 'Relationale Datenbanken und SQL',
                'semester': 3,
                'course_type': CourseType.VORLESUNG,
                'discipline': Discipline.INFORMATIK,
                'lpo_relevance': LPO.LPO_I,
                'ects': 6,
                'sws': 4,
                'max_participants': 80,
                'order': 6
            },
            {
                'name': 'Softwareengineering',
                'description': 'Methoden der Softwareentwicklung',
                'semester': 4,
                'course_type': CourseType.VORLESUNG,
                'discipline': Discipline.INFORMATIK,
                'lpo_relevance': LPO.LPO_I,
                'ects': 6,
                'sws': 4,
                'max_participants': 70,
                'order': 7
            },
            {
                'name': 'Grundlagen der Statistik',
                'description': 'Deskriptive und induktive Statistik',
                'semester': 3,
                'course_type': CourseType.VORLESUNG,
                'discipline': Discipline.MATHEMATIK,
                'lpo_relevance': LPO.LPO_I,
                'ects': 6,
                'sws': 4,
                'max_participants': 60,
                'order': 8
            }
        ]
        
        courses = []
        for course_data in courses_data:
            course, created = Course.objects.get_or_create(
                name=course_data['name'],
                defaults=course_data
            )
            courses.append(course)
            if created:
                self.stdout.write(f'Created course: {course.name}')
        
        # Create sample modules
        modules_data = [
            {
                'name': 'Grundlagen der Informatik',
                'description': 'Einführung in die Informatik und Programmierung',
                'order': 1,
                'course_names': ['Einführung in die Informatik', 'Praktikum Programmierung']
            },
            {
                'name': 'Mathematische Grundlagen',
                'description': 'Mathematik für Informatiker',
                'order': 2,
                'course_names': ['Mathematik für Informatiker I', 'Grundlagen der Statistik']
            },
            {
                'name': 'Programmierung und Algorithmen',
                'description': 'Vertiefung in Programmierung und Algorithmen',
                'order': 3,
                'course_names': ['Programmierparadigmen', 'Algorithmen und Datenstrukturen']
            },
            {
                'name': 'Angewandte Informatik',
                'description': 'Praktische Anwendung der Informatik',
                'order': 4,
                'course_names': ['Datenbanksysteme', 'Softwareengineering']
            }
        ]
        
        modules = []
        for module_data in modules_data:
            module, created = Module.objects.get_or_create(
                name=module_data['name'],
                defaults={
                    'description': module_data['description'],
                    'order': module_data['order']
                }
            )
            
            if created:
                # Add courses to module
                for course_name in module_data['course_names']:
                    try:
                        course = Course.objects.get(name=course_name)
                        module.courses.add(course)
                    except Course.DoesNotExist:
                        self.stdout.write(f'Warning: Course {course_name} not found')
                
                self.stdout.write(f'Created module: {module.name}')
            
            modules.append(module)
        
        # Create sample programme
        programme, created = Programme.objects.get_or_create(
            name='Bachelor Informatik',
            defaults={
                'programme_type': ProgrammeType.BACHELOR,
            }
        )
        
        if created:
            # Add all modules to the programme
            for module in modules:
                programme.modules.add(module)
            self.stdout.write(f'Created programme: {programme.name}')
        
        # Create sample revision
        revision, created = Revision.objects.get_or_create(
            name='Studienplan 2025',
            defaults={
                'author': user,
                'order': 1
            }
        )
        
        if created:
            revision.programmes.add(programme)
            self.stdout.write(f'Created revision: {revision.name}')
        
        self.stdout.write(self.style.SUCCESS('Sample data created successfully!'))
        self.stdout.write('You can now view the data at:')
        self.stdout.write('- http://localhost:8000/v2/courses/')
        self.stdout.write('- http://localhost:8000/v2/modules/')
        self.stdout.write('- http://localhost:8000/v2/programmes/')
        self.stdout.write('- http://localhost:8000/v2/revisions/')
