import 'lazysizes';

import Resolver from './resolver';
import Locations from './locations';
import Router from './router';
import ViewSwitcher from './view-switcher';

import Settings from '../models/settings';

import LocationChooser from '../views/location-chooser';
import EventsView from '../views/events-view';
import PlacesView from '../views/places-view';
import SingleEventView from '../views/single-event-view';
import SinglePlaceView from '../views/single-place-view';
import NotFoundView from '../views/not-found';

import {show, hide} from '../utils';


export default class App {
  constructor() {
    this.settings = new Settings();
    this.locations = new Locations();

    this.resolver = new Resolver();
    this.resolver.addRoute('index', '/');
    this.resolver.addRoute('location', '/{location:[a-z\-]+}/');
    this.resolver.addRoute('events', '/{location:[a-z\-]+}/events/');
    this.resolver.addRoute(
      'events',
      '/{location:[a-z\-]+}/events/{date:\\d\\d\\d\\d-\\d\\d-\\d\\d}/');
    this.resolver.addRoute('places', '/{location:[a-z\-]+}/places/');
    this.resolver.addRoute('single-event', '/event/{id:\\d+}/');
    this.resolver.addRoute('single-place', '/place/{id:\\d+}/');

    this.router = new Router(this.resolver);
    this.router.addHandler('index', this.visitIndex.bind(this));
    this.router.addHandler('location', this.visitLocation.bind(this));
    this.router.addHandler('events', this.visitEvents.bind(this));
    this.router.addHandler('places', this.visitPlaces.bind(this));
    this.router.addHandler('single-event', this.visitSingleEvent.bind(this));
    this.router.addHandler('single-place', this.visitSinglePlace.bind(this));
    this.router.setNotFoundHandler(this.notFound.bind(this));

    const viewContainer = document.querySelector('#view-container');
    this.viewSwitcher = new ViewSwitcher(this, viewContainer);
  }

  run() {
    this.settings.fetch().then(() => {
      this.setupLocationChooser();
      this.router.redirect(window.location.pathname);
    });
  }

  setupLocationChooser() {
    const locationContainer = document.querySelector('#city');
    const locationChooser = new LocationChooser({app: this});
    locationChooser.render();
    locationContainer.appendChild(locationChooser.element);
    show(locationContainer);
  }

  setTitle(title) {
    this.viewSwitcher.setTitle(title);
  }

  // route handlers

  visitIndex() {
    const location = this.settings.get('location');
    const path = this.resolver.reverse('events', {location});
    this.router.redirect(path);
  }

  visitLocation({location}) {
    const path = this.resolver.reverse('events', {location});
    this.router.redirect(path);
  }

  visitEvents(args) {
    this.viewSwitcher.switchView(EventsView, args);
  }

  visitPlaces(args) {
    this.viewSwitcher.switchView(PlacesView, args);
  }

  visitSingleEvent(args) {
    this.viewSwitcher.switchView(SingleEventView, args);
  }

  visitSinglePlace(args) {
    this.viewSwitcher.switchView(SinglePlaceView, args);
  }

  notFound() {
    this.viewSwitcher.switchView(NotFoundView);
  }
}
