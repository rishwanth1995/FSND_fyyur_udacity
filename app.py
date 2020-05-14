#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, jsonify
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from flask_wtf.csrf import CsrfProtect
from forms import *
from flask_migrate import Migrate
import sys
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

csrf = CsrfProtect()
csrf.init_app(app)
migrate = Migrate(app, db)


#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#


class Show(db.Model):
    __tablename__ = 'Show'
    id = db.Column(db.Integer, primary_key = True)
    venue_id = db.Column(db.Integer, db.ForeignKey(
        'Venue.id'), nullable = False)
    artist_id = db.Column(db.Integer, db.ForeignKey(
        'Artist.id'), nullable = False)
    start_time = db.Column(db.DateTime(timezone=True))


class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    website_link = db.Column(db.String(500))
    seeking_talent = db.Column(db.Boolean, nullable=False, default=False)
    shows = db.relationship('Show', backref="venue", lazy=True)



class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website_link = db.Column(db.String(500))
    seeking_performance = db.Column(db.Boolean, nullable=False, default=False)
    shows = db.relationship('Show', backref="artist", lazy=True)




#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#


def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format)


app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#


@app.route('/', methods=['GET'])
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():

    areas = Venue.query.with_entities(func.count(Venue.id), Venue.city, Venue.state).group_by(Venue.city, Venue.state).all()
    data = []
    for area in areas:
          area_dict = {}
          area_dict['city'] = area.city
          area_dict['state'] = area.state
          venues = Venue.query.filter_by(state=area.state).filter_by(city=area.city).order_by('id').all()
          venues_data = [] 
          for venue in venues:
                venue_dict = {}
                venue_dict['id'] = venue.id
                venue_dict['name'] = venue.name
                venue_dict['num_upcoming_shows'] = len(Show.query.filter(Show.venue_id==venue.id).filter(Show.start_time>datetime.now()).all())
                venues_data.append(venue_dict)
          area_dict['venues'] = venues_data
          data.append(area_dict)
    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():

    
    venue_query = db.session.query(Venue).filter(Venue.name.ilike("%"  + request.form['search_term'] + "%")).all()
    
    response = {}
    data = []
    for venue in venue_query:
          temp = {}
          temp['id'] = venue.id
          temp['name'] = venue.name
          data.append(temp)
    response['count'] = len(venue_query)
    response['data'] = data

    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):

    venue_query = db.session.query(Venue).get(venue_id)
    
    if not venue_query:
          return render_template('errors/404.html')
    
    past_shows_results = db.session.query(Show).join(Artist).filter(Show.venue_id==venue_id).filter(Show.start_time<=datetime.now()).all()
    upcoming_shows_results = db.session.query(Show).join(Artist).filter(Show.venue_id==venue_id).filter(Show.start_time>datetime.now()).all()
    
    data = {}
    
    
    data['id'] = venue_query.id
    data['name'] = venue_query.name
    data['genres'] = venue_query.genres.split(',')
    data['address'] = venue_query.address
    data['city'] = venue_query.city
    data['state'] = venue_query.state
    data['phone'] = venue_query.phone
    data['website'] = venue_query.website_link
    data['facebook_link'] = venue_query.facebook_link
    data['seeking_talent'] = venue_query.seeking_talent
    if (bool(venue_query.seeking_talent)):
          data['seeking_description'] = "We are on the lookout for a local artist to play every two weeks. Please call us."
    data['image_link'] = venue_query.image_link
    
    past_shows = []
    for item in past_shows_results:
          temp = {}
          temp['artist_id'] = item.artist_id
          temp['artist_name'] = item.artist.name
          temp['artist_image_link'] = item.artist.image_link
          temp['start_time'] = item.start_time.strftime('%Y-%m-%d %H:%M:%S')
          past_shows.append(temp)

    data['past_shows'] = past_shows
    data['past_shows_count'] = len(past_shows)
    upcoming_shows = []
    for item in upcoming_shows_results:
          temp = {}
          temp['artist_id'] = item.artist_id
          temp['artist_name'] = item.artist.name
          temp['artist_image_link'] = item.artist.image_link
          temp['start_time'] = item.start_time.strftime('%Y-%m-%d %H:%M:%S')
          upcoming_shows.append(temp)    
    
    data['upcoming_shows'] = upcoming_shows
    data['upcoming_shows_count'] = len(upcoming_shows)
          
    

    return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------


# @app.route('/venues/create', methods=['GET'])
# def create_venue_form():
#     form = VenueForm()
#     return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['GET', 'POST'])
def create_venue_submission():

    form = VenueForm()
    if form.validate_on_submit():
          error = False
          try:
            venue = Venue(name=request.form['name'],
                            city=request.form['city'],
                            state=request.form['state'],
                            address=request.form['address'],
                            phone=request.form['phone'],
                            image_link=request.form['image_link'],
                            website_link=request.form['website_link'],
                            facebook_link=request.form['facebook_link'],
                            genres=",".join(request.form.getlist('genres'))
                            )
            db.session.add(venue)
            db.session.commit()
          except:
            db.session.rollback()
            error = True
          finally:
            db.session.close()

          if error:
            flash('An error occured. Venue ' +
                    request.form['name'] + 'could not be listed.')
          else:
              flash('Venue ' + request.form['name'] +
                    ' was successfully listed!')

          return render_template('pages/home.html')
    else:
          for field in form.errors:
                flash(form.errors[field])
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):

    try:
      venue = Venue.query.get(venue_id)
      db.session.delete(venue)
      db.session.commit()
      flash('Venue ' + venue.name + ' was deleted')
    except:
      flash('an error occured and Venue ' + venue.name + ' was not deleted')
      db.session.rollback()
    finally:
      db.session.close()
    
    return jsonify({ 'success': True })

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
    artists = Artist.query.all()
    data = []
    for artist in artists:
          artist_dict = {}
          artist_dict['id'] = artist.id
          artist_dict['name'] = artist.name
          data.append(artist_dict)
          

    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
 
    
    artist_query = db.session.query(Artist).filter(Artist.name.ilike("%"  + request.form['search_term'] + "%")).all()
    
    response = {}
    data = []
    for artist in artist_query:
          temp = {}
          temp['id'] = artist.id
          temp['name'] = artist.name
          data.append(temp)
    response['count'] = len(artist_query)
    response['data'] = data

    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):

    artist_query = db.session.query(Artist).get(artist_id)
    
    if not artist_query:
          return render_template('errors/404.html')
        
    past_shows_results = db.session.query(Show).join(Artist).filter(Show.venue_id==artist_id).filter(Show.start_time<=datetime.now()).all()
    upcoming_shows_results = db.session.query(Show).join(Artist).filter(Show.venue_id==artist_id).filter(Show.start_time>datetime.now()).all()
    
    data = {}
    
    data['id'] = artist_query.id
    data['name'] = artist_query.name
    data['genres'] = artist_query.genres.split(',')
    data['website'] = artist_query.website_link
    data['facebook_link'] = artist_query.facebook_link
    data['seeking_venue'] = artist_query.seeking_performance
    if bool(artist_query.seeking_performance):
          data['seeking_description'] = "Looking for shows to perform at in the San Francisco Bay Area!"
    data['city'] = artist_query.city
    data['state'] = artist_query.state
    data['phone'] = artist_query.phone
    
    data['upcoming_shows_count'] = len(upcoming_shows_results)
    data['past_shows_count'] = len(past_shows_results)
    
    past_shows = []
    
    for item in past_shows_results:
          temp = {}
          temp['artist_id'] = item.artist_id
          temp['artist_name'] = item.artist.name
          temp['artist_image_link'] = item.artist.image_link
          temp['start_time'] = item.start_time.strftime('%Y-%m-%d %H:%M:%S')
          past_shows.append(temp)
    
    upcoming_shows = []
    for item in upcoming_shows_results:
          temp = {}
          temp['artist_id'] = item.artist_id
          temp['artist_name'] = item.artist.name
          temp['artist_image_link'] = item.artist.image_link
          temp['start_time'] = item.start_time.strftime('%Y-%m-%d %H:%M:%S')
          upcoming_shows.append(temp)
    
    data['upcoming_shows'] = upcoming_shows
    data['past_shows'] = past_shows
    
    return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    artist_result = db.session.query(Artist).get(artist_id)
    artist = {
        "id": artist_result.id,
        "name": artist_result.name,
        "genres": artist_result.genres.split(","),
        "city": artist_result.city,
        "state": artist_result.state,
        "phone": artist_result.phone,
        "website": artist_result.website_link,
        "facebook_link": artist_result.facebook_link,
        "seeking_performance": artist_result.seeking_performance,              
        "image_link": artist_result.image_link
    }
    if bool(artist_result.seeking_performance):
        artist['seeking_description'] = "Looking for shows to perform at " + artist['city'] + "," +  artist['state'] + " area",
    form.state.default = artist['state']
    form.process()
    
    form.genres.default = artist['genres']
    form.process()
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):

    try:
      artist = db.session.query(Artist).get(artist_id)
      artist.name = request.form['name']
      artist.city = request.form['city']
      artist.state = request.form['state']
      artist.phone = request.form['phone']
      artist.facebook_link = request.form['facebook_link']
      artist.website_link = request.form['website_link']
      artist.image_link = request.form['image_link']
      db.session.commit()
    except:
      db.session.rollback()
      print(sys.exc_info())
    finally:
      db.session.close()

    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    venue_result = db.session.query(Venue).get(venue_id)
    venue = {
        "id": venue_result.id,
        "name": venue_result.name,
        "genres": venue_result.genres.split(","),
        "address": venue_result.address,
        "city": venue_result.city,
        "state": venue_result.state,
        "phone": venue_result.phone,
        "website": venue_result.website_link,
        "facebook_link": venue_result.facebook_link,
        "seeking_talent": venue_result.seeking_talent,              
        "image_link": venue_result.image_link
    }
    if bool(venue_result.seeking_talent):
        venue['seeking_description'] = "We are on the lookout for a local artist to play every two weeks. Please call us.",
    form.state.default = venue['state']
    form.process()
    
    form.genres.default = venue['genres']
    form.process()
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):

    try:
      venue = db.session.query(Venue).get(venue_id)
      venue.name = request.form['name']
      venue.city = request.form['city']
      venue.address = request.form['address']
      venue.state = request.form['state']
      venue.phone = request.form['phone']
      venue.facebook_link = request.form['facebook_link']
      venue.website_link = request.form['website_link']
      venue.image_link = request.form['image_link']
      db.session.commit()
    except:
      db.session.rollback()
      print(sys.exc_info())
    finally:
      db.session.close()
    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------



@app.route('/artists/create', methods=['GET','POST'])
def create_artist_submission():
    form = ArtistForm()
    if form.validate_on_submit():
        error = False
        try:
            artist = Artist(name=request.form['name'],
                            city=request.form['city'],
                            state=request.form['state'],
                            phone=request.form['phone'],
                            image_link=request.form['image_link'],
                            website_link=request.form['website_link'],
                            facebook_link=request.form['facebook_link'],
                            genres=",".join(request.form.getlist('genres'))
                            )
            db.session.add(artist)
            db.session.commit()
        except:
            db.session.rollback()
            error = True
            print(sys.exc_info())
        finally:
            db.session.close()

        if error:
            flash('An error occured. Artist ' +
                  request.form['name'] + 'could not be listed.')
        else:
            flash('Artist ' + request.form['name'] + ' was successfully listed!')
        return render_template('pages/home.html')
    else:
        for field in form.errors:
              flash(form.errors[field])
    return render_template('forms/new_artist.html', form=form)


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():

    shows = db.session.query(Show).join(Artist).join(Venue).all()
    print(shows)
    data = []
    for show in shows:
          show_dict = {}
          show_dict['venue_id'] = show.venue_id
          show_dict['venue_name'] = show.venue.name
          show_dict['artist_id'] = show.artist_id
          show_dict['artist_name'] = show.artist.name
          show_dict['artist_image_link'] = show.artist.image_link
          show_dict['start_time'] = show.start_time.strftime('%Y-%m-%d %H:%M:%S')
          data.append(show_dict)
                    

    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():

    error = False
    try:
        show = Show(venue_id=request.form['venue_id'],
                    artist_id=request.form['artist_id'],
                    start_time=request.form['start_time'])
        db.session.add(show)
        db.session.commit()
    except:
        db.session.rollback()
        error = True
        print(sys.exc_info())
    finally:
        db.session.close()

    if error:
        flash('An error occured, show could not be listed')
    else:
        flash('Show was successfully listed!')


    return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
