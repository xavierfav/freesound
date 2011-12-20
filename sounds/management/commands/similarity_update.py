from django.core.management.base import NoArgsCommand
from sounds.models import Sound
from similarity.client import Similarity

class Command(NoArgsCommand):
    help = "Take all sounds that haven't been added to the similarity service yet and add them."

    def handle(self, **options):
        to_be_added = Sound.objects.filter(analysis_state='OK', similarity_state='PE', moderation_state='OK')
        for sound in to_be_added:
            try:
                Similarity.add(sound.id, sound.locations('analysis.statistics.path'))
                #sound.similarity_state = 'OK'
                sound.set_similarity_state('OK')
            except Exception, e:
                print 'Sound could not be added: \n\t%s' % str(e)
                #sound.similarity_state = 'FA'
                sound.set_similarity_state('FA')
            #sound.save()
