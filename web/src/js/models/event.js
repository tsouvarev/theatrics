import moment from 'moment';

import locations from '../core/locations';
import Model from '../base/model';
import {capfirst, range, makeAbsoluteURL} from '../utils';

import Place from './place';
import Date from './date';
import Price from './price';


export default class Event extends Model {
  getName() {
    return this.data.name || this.getFullName();
  }

  getFullName() {
    return capfirst(this.data.full_name);
  }

  getParent() {
    if (this.data.parent) return new Event(this.data.parent);
  }

  getPlace() {
    if (this.data.place) return new Place(this.data.place);
  }

  getPrice() {
    if (this.data.price.text) return new Price(this, this.data.price);
  }

  getLocation() {
    return locations.get(this.data.location);
  }

  getDisplayDuration() {
    const durations = this.getDisplayDates().map(date => date.getDuration());
    const [first, ...others] = durations;
    if (others.every(duration => duration.asMinutes() == first.asMinutes())) {
      return first;
    } else {
      return undefined;
    }
  }

  getDisplayDates() {
    const allDates = this.getDates();
    const actualDates = allDates.filter(date => date.isActual())
    return actualDates.length ? actualDates : allDates;
  }

  getDates() {
    return this.data.dates.map(spec => new Date(this, spec));
  }

  hasChildren() {
    return this.data.children_count > 0;
  }

  isPremiere() {
    return this.data.is_premiere;
  }

  isFestival() {
    return this.data.kind == 'festival';
  }

  isExhibition() {
    return this.data.kind == 'exhibition';
  }

  isActual() {
    const timezone = this.getLocation().timezone;
    const isDateBased = this.data.end.length == 10;
    const end = moment.tz(this.data.end, timezone);
    const endBound = isDateBased ? end.clone().add(1, 'day') : end;
    return endBound.isAfter(moment());
  }

  getSchemaOrgType() {
    if (this.isFestival()) {
      return 'Festival';
    } else if (this.isExhibition()) {
      return 'ExhibitionEvent';
    } else {
      return 'TheaterEvent';
    }
  }
}


export function eventsToDates(events) {
  return events
    .map(event => event.getDates())
    .reduce((a, b) => a.concat(b), [])
    .sort((date1, date2) => date1.start.unix() - date2.start.unix());
}
