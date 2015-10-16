var gulp = require('gulp');
var postcss = require('gulp-postcss');
var source = require('vinyl-source-stream');
var buffer = require('vinyl-buffer');
var browserify = require('browserify');
var babelify = require('babelify');
var watchify = require('watchify');
var util = require('gulp-util');
var handlebars = require('gulp-compile-handlebars');
var rename = require('gulp-rename');


function logError(e) {
  util.log(util.colors.red('Error'), e.message);
}


/* CSS */

gulp.task('build-css', function() {
  return gulp.src('client/css/**/*.css')
    .on('error', logError)
    .pipe(postcss([
      require('postcss-import')(),
      require('autoprefixer')()
    ]))
    .pipe(gulp.dest('client/build'));
});


gulp.task('watch-css', function () {
  gulp.start(['build-css']);
  gulp.watch('client/css/**/*.css', ['build-css']);
});


/* JS */

function buildBrowserify(options) {
  var b = browserify({
    entries: 'client/js/' + options.entry,
    debug: true,
    //these properties are needed for watchify
    cache: {},
    packageCache: {}
  });

  var buildBundle = function() {
    return b.bundle()
      .on('error', logError)
      .pipe(source(options.entry))
      .pipe(buffer())
      .pipe(gulp.dest('client/build'));
  };

  if (options.watch) {
    b = watchify(b);
  }

  b.on('update', buildBundle);
  b.transform(babelify);

  return buildBundle();
}

gulp.task('build-js', function () {
  return buildBrowserify({
    entry: 'index.js',
  });
});

gulp.task('watch-js', function () {
  buildBrowserify({
    entry: 'index.js',
    watch: true
  });
});


/* HTML */

gulp.task('build-html', function() {
  var context = {}
  var options = {}
  return gulp.src('client/*.hbs')
    .on('error', logError)
    .pipe(handlebars(context, options))
    .pipe(rename({extname: '.html'}))
    .pipe(gulp.dest('client/build'));
});

gulp.task('watch-html', function() {
  gulp.start(['build-html']);
  gulp.watch('client/*.hbs', ['build-html']);
});


/* Big tasks */

gulp.task('watch', function () {
  gulp.start('watch-css');
  gulp.start('watch-js');
  gulp.start('watch-html');
});

gulp.task('build', ['build-css', 'build-js', 'build-html']);
