import csv
from django.core.management.base import BaseCommand
from movies.models import Rating, Content
from django.contrib.auth.models import User
from users.models import Profile  

class Command(BaseCommand):
    help = 'Export user-content ratings, item and user features to CSV for GNN model'

    def handle(self, *args, **kwargs):
        # === 1. Export interactions ===
        with open('gnn/interact.csv', 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['userId', 'movieId', 'rating'])

            for r in Rating.objects.select_related("user", "content").all():
                writer.writerow([r.user.id, r.content.id, r.rating])
        self.stdout.write(self.style.SUCCESS('interact.csv exported'))

        all_genres = set()
        for content in Content.objects.all():
            all_genres.update(content.genres)
        genre_list = sorted(list(all_genres))

        with open('item_feat.csv', 'w', newline='') as file:
            writer = csv.writer(file)
            header = ['movieId', 'type_MOVIE', 'type_TV_SHOW', 'type_ANIME', 'is_animated'] + genre_list
            writer.writerow(header)

            for c in Content.objects.all():
                type_flags = [int(c.type == 'MOVIE'), int(c.type == 'TV_SHOW'), int(c.type == 'ANIME')]
                is_animated = int(c.is_animated)
                genre_flags = [int(g in c.genres) for g in genre_list]
                row = [c.id] + type_flags + [is_animated] + genre_flags
                writer.writerow(row)
        self.stdout.write(self.style.SUCCESS('item_feat.csv exported'))

     
with open('user_feat.csv', 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['userId', 'F', 'M'])

    for user in User.objects.all():
        try:
            profile = user.profile
            gender = getattr(profile, 'gender', '').upper()
            if gender == 'F':
                F, M = 1, 0
            elif gender == 'M':
                F, M = 0, 1
            else:
                F, M = 0, 0  
        except Profile.DoesNotExist:
            F, M = 0, 0
        writer.writerow([user.id, F, M])

