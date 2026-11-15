import factory
from django.contrib.auth import get_user_model

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ('email',)
        skip_postgeneration_save = True

    email = factory.Sequence(lambda n: f'user{n}@example.com')
    username = factory.Sequence(lambda n: f'user{n}')

    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        raw_password = extracted or 'TestPass123!'
        self.set_password(raw_password)

        if create:
            self.save(update_fields=['password'])

    is_active = True
