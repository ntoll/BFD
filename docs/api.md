# BFD API

Interactions with the Big Friendly Datastore are via a
[REST-ful API](https://en.wikipedia.org/wiki/Representational_state_transfer)
described below.

The five core concepts needed to understand the API are:

1. *Users* - real humans who interact with the BFD. Admin users are able to
   create new users. All users interact with the BFD via the API and use either
   token-based HTTP authentication via an HTTP `Authorization` header in all
   requests, or via session management if interacting with the BFD via its
   browser based frontend.
2. *Namespaces* - define who is annotating data. Namespaces have a unique name
   and a free text description to provide context. Users are automatically
   given a namespace with the same name as their username. Further namespaces
   may be created to represent organisational units. Namespaces must have at
   least one user, and potentially many users, to act as administrators. They
   define the tags and the permissions relating to tags that belong to the
   Namespace.
3. *Tags* - define what is annotated to objects. Tags belong to a parent
   namespace, so it's possible to understand who is annotating what within the
   BFD. Tags have a name that is unique within the parent namespace and a
   free text description to provide context. Tags can be either public (anyone
   can read values associated with them) or private (only whitelisted
   individuals can read values annotated with them). Furthermore, only
   namespace admins or those users listed in a "users" whitelist are able to
   use the tag to annotate values onto an object. Finally, tags are typed so
   if a tag is for storing a date-time value, an operation to use it to
   annotate a string value will fail.
4. *Objects* - represent things in the universe. Objects are identified by a
   unique name. What an object represents can be found out by looking at the
   aggregation of values annotated to the object via BFD's user's namespaces
   and tags.
5. *Values* - are the data associated with an object via a namespace/tag
   combination. Values can be used with [the query language](query.md) to find
   objects of interest.

## Users

`GET /u/<username>`

Returns limited information about the user identified by `username`. Admin
users and the user identified by `username` see a more comprehensive profile.

`POST /u/<username>`

Use JSON data to update the referenced user. Only works if the request is made
by an admin user of the user identified by `username`.

`POST /u/new`

Creates a new user from the JSON data provided by an admin user.

## Namespaces

`GET /n/<namespace>`

Returns the description associated with the referenced `namespace`.

`PUT /n/<namespace>`

Use JSON data to update the referenced `namespace`. Only works if the request
is made by a global admin user or a user listed as the referenced namespace's
admin.

`POST /n/new`

Creates a new namespace from the JSON data provided by an admin user.

## Tags

`GET /t/<namespace>/<tag>`

Returns the description associated with the referenced `namespace` / `tag`
pair.

`PUT /t/<namespace>/<tag>`

Use JSON data to update the referenced `namespace` / `tag` pair. Only works if
the request is made by a global admin user or a user listed as the referenced
namespace's admin.

`POST /t/<namespace>/new`

Creates a new namespace from the JSON data provided by a global admin user or
a user listed as the referenced namespace's admin.

## Objects, Tags and Values

`GET /o/<object_id>/<namespace>/<tag>`

Get the value annotated by the referenced `namespace` / `tag` pair on the
referenced `object`. Will return 404 if the value doesn't exist or if the
callee doesn't have read permission for the referenced `tag`.

`POST /o/<object_id>/<namespace>/<tag>`

Annotate the value in the request, using the `namespace` / `tag` pair onto the
referenced `object`. Will only work for global admins, namespace admins or
those with `use` permission for the referenced tag.

`DELETE /o/<object_id>/<namespace>/<tag>`

Remove the value annotated on the referenced object by the namespace/tag pair.
Will only work if the user has "use" permission on the referenced tag.

`GET /o/<object_id>`

Get a list of visible namespace/tag pairs on the referenced object.

`POST /o/<object_id>`

Annotate a list of `namespace/tag: value` pairs onto the referenced object.
Will only work if the user has permission to annotate with all the referenced
namespace / tag pairs.

`POST /o/<object_id>/delete`

Delete a list of `namespace/tag` annotations from the referenced object.

`POST /o/select`

Select a list of namespace/tag pairs from objects matching a query. Expressed
as a JSON object.

`POST /o/update`

Update a list of `namespace/tag: value` pairs onto objects matching a query.
Expressed as a JSON object.

`POST /o/delete`

Delete a list of `namespace/tag` pairs from objects matching a query. Expressed
as a JSON object.

`POST /o/bulk`

Bulk annotate a collection of specified objects with associated object specific
`namespace/tag: value` pairs. Expressed as a JSON object. This is how to do
bulk imports/updates.
