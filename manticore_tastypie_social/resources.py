from manticore_tastypie_core.manticore_tastypie_core.resources import ManticoreModelResource
from manticore_tastypie_social.manticore_tastypie_social.models import Tag


class TagResource(ManticoreModelResource):

    class Meta:
        queryset = Tag.objects.all()
        fields = ['id','name',]
        resource_name = "tag"
        object_name = "tag"
        include_resource_uri = False